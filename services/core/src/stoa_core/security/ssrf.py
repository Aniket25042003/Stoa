"""SSRF guards for server-side HTTP fetches."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

_BLOCKED_NETWORKS = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)


def _ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return any(ip in net for net in _BLOCKED_NETWORKS)


def _resolve_host_ips(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for info in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM):
        ips.append(ipaddress.ip_address(info[4][0]))
    return ips


def assert_safe_fetch_url(url: str) -> str:
    """Validate URL is safe for server-side fetch. Raises ValueError if not."""
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        raise ValueError("Only https URLs are allowed")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a hostname")
    if hostname.lower() in {"localhost", "metadata.google.internal"}:
        raise ValueError("Blocked hostname")
    if hostname.endswith(".internal") or hostname.endswith(".local"):
        raise ValueError("Blocked hostname")

    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        for ip in _resolve_host_ips(hostname):
            if _ip_blocked(ip):
                raise ValueError("Hostname resolves to blocked IP address") from None
        return url

    if _ip_blocked(literal):
        raise ValueError("Blocked IP address")
    return url
