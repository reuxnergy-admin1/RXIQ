"""Tests for URL validation and SSRF protection."""

from __future__ import annotations

import pytest

from app.services.url_validator import URLValidationError, validate_url


class TestURLValidation:
    """URL validation and security tests."""

    # ── Valid URLs ──

    def test_valid_http_url(self):
        result = validate_url("http://example.com")
        assert result == "http://example.com"

    def test_valid_https_url(self):
        result = validate_url("https://example.com/path?q=test")
        assert result == "https://example.com/path?q=test"

    def test_valid_url_with_port(self):
        result = validate_url("https://example.com:8080/api")
        assert result == "https://example.com:8080/api"

    # ── Blocked schemes ──

    def test_blocks_ftp_scheme(self):
        with pytest.raises(URLValidationError, match="Invalid URL scheme"):
            validate_url("ftp://example.com/file")

    def test_blocks_file_scheme(self):
        with pytest.raises(URLValidationError, match="Invalid URL scheme"):
            validate_url("file:///etc/passwd")

    def test_blocks_javascript_scheme(self):
        with pytest.raises(URLValidationError, match="Invalid URL scheme"):
            validate_url("javascript:alert(1)")

    def test_blocks_data_scheme(self):
        with pytest.raises(URLValidationError, match="Invalid URL scheme"):
            validate_url("data:text/html,<h1>test</h1>")

    # ── SSRF: private/internal IPs ──

    def test_blocks_localhost(self):
        with pytest.raises(URLValidationError, match="private|internal"):
            validate_url("http://127.0.0.1/admin")

    def test_blocks_localhost_hostname(self):
        with pytest.raises(URLValidationError, match="private|internal"):
            validate_url("http://localhost/admin")

    def test_blocks_private_10_range(self):
        with pytest.raises(URLValidationError, match="private|internal"):
            validate_url("http://10.0.0.1/secret")

    def test_blocks_private_172_range(self):
        with pytest.raises(URLValidationError, match="private|internal"):
            validate_url("http://172.16.0.1/secret")

    def test_blocks_private_192_range(self):
        with pytest.raises(URLValidationError, match="private|internal"):
            validate_url("http://192.168.1.1/admin")

    # ── SSRF: cloud metadata endpoints ──

    def test_blocks_aws_metadata(self):
        with pytest.raises(URLValidationError):
            validate_url("http://169.254.169.254/latest/meta-data/")

    def test_blocks_gcp_metadata(self):
        with pytest.raises(URLValidationError):
            validate_url("http://metadata.google.internal/computeMetadata/v1/")

    # ── Missing/empty hostname ──

    def test_blocks_empty_hostname(self):
        with pytest.raises(URLValidationError, match="hostname"):
            validate_url("http:///path")

    # ── Unresolvable domains ──

    def test_blocks_unresolvable_domain(self):
        with pytest.raises(URLValidationError, match="resolve"):
            validate_url("https://this-domain-definitely-does-not-exist-xyz123.com")
