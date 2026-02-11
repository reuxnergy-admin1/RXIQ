"""URL validation and security utilities.

Prevents SSRF attacks, blocks internal network access, and validates URLs
before scraping.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

from app.config import get_settings

settings = get_settings()

# Private/reserved IP ranges that must never be scraped
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

# Schemes we allow
_ALLOWED_SCHEMES = {"http", "https"}

# Default blocked hostname patterns (cloud metadata endpoints, etc.)
_ALWAYS_BLOCKED_HOSTS = {
    "metadata.google.internal",
    "169.254.169.254",  # AWS/GCP metadata
    "metadata.azure.internal",
}


class URLValidationError(Exception):
    """Raised when a URL fails security validation."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def validate_url(url: str) -> str:
    """
    Validate and sanitize a URL for scraping.

    Checks:
    - Valid scheme (http/https only)
    - Not targeting internal/private networks (SSRF protection)
    - Not on blocked hosts list
    - Not matching blocked patterns from config
    - Resolvable hostname

    Returns:
        The validated URL string.

    Raises:
        URLValidationError if the URL fails any check.
    """
    parsed = urlparse(url)

    # Check scheme
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise URLValidationError(
            f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed."
        )

    # Check hostname exists
    hostname = parsed.hostname
    if not hostname:
        raise URLValidationError("URL must include a valid hostname.")

    # Check against always-blocked hosts
    if hostname.lower() in _ALWAYS_BLOCKED_HOSTS:
        raise URLValidationError("Access to this host is not permitted.")

    # Check against user-configured blocked patterns
    for pattern in settings.blocked_url_patterns_list:
        if pattern and re.search(pattern, url, re.IGNORECASE):
            raise URLValidationError("This URL matches a blocked pattern.")

    # Resolve hostname and check IP ranges (SSRF protection)
    try:
        addr_infos = socket.getaddrinfo(
            hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM
        )
        for family, _, _, _, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
                for network in _BLOCKED_NETWORKS:
                    if ip in network:
                        raise URLValidationError(
                            "Access to private/internal network addresses is not permitted."
                        )
            except ValueError:
                continue
    except socket.gaierror:
        raise URLValidationError(f"Could not resolve hostname '{hostname}'.")

    return url


def sanitize_url_for_logging(url: str) -> str:
    """Remove sensitive query parameters from URL for safe logging."""
    parsed = urlparse(url)
    # Strip query and fragment for logging — keeps just scheme + host + path
    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if len(clean) > 200:
        clean = clean[:200] + "..."
    return clean
