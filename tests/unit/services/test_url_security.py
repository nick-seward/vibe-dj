from unittest.mock import patch

import pytest

from vibe_dj.services.url_security import UnsafeOutboundURLError, validate_outbound_url


class TestValidateOutboundUrl:
    """Test suite for outbound URL SSRF safety validation."""

    def test_allows_public_literal_ip(self):
        """Public literal IPs should be allowed."""
        assert validate_outbound_url("http://8.8.8.8:4533") == "http://8.8.8.8:4533"

    def test_rejects_empty_url(self):
        """Empty URLs should be rejected."""
        with pytest.raises(UnsafeOutboundURLError, match="cannot be empty"):
            validate_outbound_url("")

    def test_rejects_non_http_scheme(self):
        """Non-http/https schemes should be rejected."""
        with pytest.raises(UnsafeOutboundURLError, match="http or https"):
            validate_outbound_url("ftp://example.com")

    def test_rejects_localhost(self):
        """localhost must be blocked."""
        with pytest.raises(UnsafeOutboundURLError, match="not allowed"):
            validate_outbound_url("http://localhost:4533")

    def test_rejects_private_literal_ip(self):
        """Private literal IPs must be blocked."""
        with pytest.raises(UnsafeOutboundURLError, match="not allowed"):
            validate_outbound_url("http://192.168.1.10:4533")

    @patch("vibe_dj.services.url_security.socket.getaddrinfo")
    def test_rejects_domain_resolving_to_private_ip(self, mock_getaddrinfo):
        """Domains resolving to private IPs must be blocked."""
        mock_getaddrinfo.return_value = [
            (2, 1, 6, "", ("10.0.0.5", 4533)),
        ]

        with pytest.raises(UnsafeOutboundURLError, match="not allowed"):
            validate_outbound_url("http://navidrome.example:4533")

    @patch("vibe_dj.services.url_security.socket.getaddrinfo")
    def test_allows_domain_resolving_to_public_ip(self, mock_getaddrinfo):
        """Domains resolving to public IPs should be allowed."""
        mock_getaddrinfo.return_value = [
            (2, 1, 6, "", ("8.8.8.8", 4533)),
        ]

        assert (
            validate_outbound_url("https://navidrome.example:4533")
            == "https://navidrome.example:4533"
        )
