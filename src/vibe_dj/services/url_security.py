import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeOutboundURLError(ValueError):
    """Raised when an outbound URL fails SSRF safety checks."""


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
        or ip.is_reserved
    )


def validate_outbound_url(url: str) -> str:
    """Validate an outbound URL to reduce SSRF risk.

    :param url: User-provided URL
    :return: Sanitized URL string safe to use for outbound requests
    :raises UnsafeOutboundURLError: If URL is malformed or points to an unsafe target
    """
    candidate = (url or "").strip()
    if not candidate:
        raise UnsafeOutboundURLError("URL cannot be empty")

    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeOutboundURLError("URL must use http or https")

    hostname = parsed.hostname
    if not hostname:
        raise UnsafeOutboundURLError("URL must include a valid hostname")

    host = hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise UnsafeOutboundURLError("Outbound URL host is not allowed")

    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None

    if literal_ip and _is_blocked_ip(literal_ip):
        raise UnsafeOutboundURLError("Outbound URL host is not allowed")

    port = parsed.port
    if port is not None and (port < 1 or port > 65535):
        raise UnsafeOutboundURLError("URL must include a valid port")

    try:
        resolved = socket.getaddrinfo(host, port or 80, type=socket.SOCK_STREAM)
    except socket.gaierror:
        resolved = []

    for info in resolved:
        ip_str = info[4][0]
        ip_obj = ipaddress.ip_address(ip_str)
        if _is_blocked_ip(ip_obj):
            raise UnsafeOutboundURLError("Outbound URL host is not allowed")

    return candidate
