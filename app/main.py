"""RXIQ API — AI-Powered Content Intelligence API.

Main FastAPI application with middleware, lifecycle management, and health checks.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.models import ErrorDetail, ErrorResponse, HealthResponse
from app.routes.v1 import router as v1_router
from app.services.cache import close_redis, init_redis, is_redis_connected

settings = get_settings()

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("rxiq")

# ──────────────────────────────────────────────
# Rate Limiting
# ──────────────────────────────────────────────

# RapidAPI sends the subscriber's key in X-RapidAPI-Proxy-Secret / X-RapidAPI-User headers.
# For standalone use, fall back to IP-based limiting.


def _get_rate_limit_key(request: Request) -> str:
    """Get rate limit key — use RapidAPI user header if present, else IP."""
    rapid_user = request.headers.get("X-RapidAPI-User")
    if rapid_user:
        return rapid_user
    return get_remote_address(request)


limiter = Limiter(key_func=_get_rate_limit_key)

# ──────────────────────────────────────────────
# App Lifecycle
# ──────────────────────────────────────────────

_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global _start_time
    _start_time = time.time()

    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize Redis
    await init_redis()

    # Initialize Sentry (optional)
    if settings.sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                traces_sample_rate=0.1,
                environment=settings.app_env,
            )
            logger.info("Sentry initialized.")
        except Exception as e:
            logger.warning(f"Sentry init failed: {e}")

    logger.info("API is ready to serve requests.")
    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_redis()


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────

API_DESCRIPTION = """
## AI-Powered Content Intelligence API

Extract, summarize, and analyze web content with a single API call.

### Endpoints

| Endpoint | Description |
|---|---|
| **POST /api/v1/extract** | Extract clean, structured text and metadata from any URL |
| **POST /api/v1/summarize** | AI-powered summarization (TL;DR, bullet points, key takeaways) |
| **POST /api/v1/sentiment** | Sentiment analysis with confidence scores and key phrases |
| **POST /api/v1/seo** | SEO metadata extraction (title, description, OG, Twitter, Schema.org) |
| **POST /api/v1/analyze** | Full analysis — all of the above in one call |

### Authentication

On RapidAPI, authentication is handled automatically via your API key.
For direct access, include your API key in the `X-API-Key` header.

### Rate Limits

| Plan | Calls/Month | Price |
|---|---|---|
| Free | 100 | $0 |
| Starter | 2,500 | $9.99/mo |
| Pro | 15,000 | $29.99/mo |
| Business | 75,000 | $99.99/mo |

### Response Format

All endpoints return a consistent JSON structure:

```json
{
  "success": true,
  "data": { ... },
  "cached": false,
  "timestamp": "2026-02-11T00:00:00Z"
}
```
"""

app = FastAPI(
    title=settings.app_name,
    description=API_DESCRIPTION,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "RXIQ API Support",
        "url": "https://rapidapi.com/rxiq/api/rxiq-api",
    },
    license_info={
        "name": "Proprietary",
    },
    servers=[
        {"url": "https://rxiq-api.p.rapidapi.com", "description": "RapidAPI Production"},
        {"url": "http://localhost:8000", "description": "Local Development"},
    ],
)

# ──────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────

# GZip compression for responses > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted hosts (prevents host-header attacks)
if settings.trusted_hosts != "*":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts_list,
    )

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def production_middleware(request: Request, call_next):
    """
    Combined production middleware:
    1. Request ID generation/forwarding
    2. RapidAPI proxy secret validation
    3. Response timing
    4. Security headers
    5. Structured request logging
    """
    # --- 1. Request ID ---
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:12]

    # --- 2. RapidAPI proxy secret validation ---
    if settings.rapidapi_proxy_secret:
        # Skip validation for health/docs/meta endpoints
        if request.url.path.startswith("/api/"):
            proxy_secret = request.headers.get("X-RapidAPI-Proxy-Secret", "")
            if proxy_secret != settings.rapidapi_proxy_secret:
                logger.warning(
                    f"Blocked request: invalid proxy secret | "
                    f"path={request.url.path} ip={request.client.host if request.client else 'unknown'}"
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "success": False,
                        "error": {
                            "code": "FORBIDDEN",
                            "message": "Unauthorized. Requests must come through RapidAPI.",
                        },
                    },
                )

    # --- 3. Timing ---
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start

    # --- 4. Response headers ---
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{elapsed:.3f}s"

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else "public, max-age=60"

    # --- 5. Structured request log ---
    if request.url.path.startswith("/api/"):
        rapid_user = request.headers.get("X-RapidAPI-User", "-")
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"time={elapsed:.3f}s "
            f"rid={request_id} "
            f"user={rapid_user}"
        )

    return response


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

app.include_router(v1_router)


# ──────────────────────────────────────────────
# Health & Meta Endpoints
# ──────────────────────────────────────────────


@app.get(
    "/",
    summary="API Info",
    description="Basic API information and links.",
    tags=["Meta"],
)
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI-Powered Content Intelligence API",
        "documentation": "/docs",
        "endpoints": {
            "extract": "/api/v1/extract",
            "summarize": "/api/v1/summarize",
            "sentiment": "/api/v1/sentiment",
            "seo": "/api/v1/seo",
            "analyze": "/api/v1/analyze",
        },
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check API health status, version, and uptime.",
    tags=["Meta"],
)
async def health_check():
    """Health check endpoint for monitoring."""
    uptime = time.time() - _start_time if _start_time else 0
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        uptime_seconds=round(uptime, 2),
        redis_connected=is_redis_connected(),
        timestamp=datetime.utcnow(),
    )


# ──────────────────────────────────────────────
# Global Exception Handler
# ──────────────────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to return consistent error format."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred. Please try again.",
                details=str(exc) if settings.app_debug else None,
            ),
        ).model_dump(mode="json"),
    )


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    """Override FastAPI's default 422 to use our error format."""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request validation failed. Check your input parameters.",
                details=str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            ),
        ).model_dump(mode="json"),
    )


# ──────────────────────────────────────────────
# Prometheus Metrics (optional)
# ──────────────────────────────────────────────

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    logger.info("Prometheus metrics enabled at /metrics")
except ImportError:
    logger.info("Prometheus metrics not available (install prometheus-fastapi-instrumentator)")
