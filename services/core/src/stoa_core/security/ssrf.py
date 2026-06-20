"""
File: services/core/src/stoa_core/security/ssrf.py
Layer: Core Security Utilities
Purpose: Implements ssrf behavior for the core security utilities.
Dependencies: standard library / local modules
"""


from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
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
    """Handles  ip blocked logic for the surrounding Stoa workflow.

    Args:
        ip (ipaddress.IPv4Address | ipaddress.IPv6Address): Input value used by this workflow step.

    Returns:
        bool: Result produced for the caller.
    """
    return any(ip in net for net in _BLOCKED_NETWORKS)


def _resolve_host_ips(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Handles  resolve host ips logic for the surrounding Stoa workflow.

    Args:
        hostname (str): Input value used by this workflow step.

    Returns:
        list[ipaddress.IPv4Address | ipaddress.IPv6Address]: Result produced for the caller.
    """
    ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for info in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM):
        ips.append(ipaddress.ip_address(info[4][0]))
    return ips


@dataclass(frozen=True)
class SafeHttpsTarget:
    """Manage SafeHttpsTarget behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    hostname: str
    ip: str
    path_with_query: str


def _path_with_query(parsed) -> str:
    """Handles  path with query logic for the surrounding Stoa workflow.

    Args:
        parsed (Any): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return path


def resolve_safe_https_target(url: str) -> SafeHttpsTarget:
    """Validate URL and pin to a resolved public IP to prevent DNS rebinding."""
    safe_url = assert_safe_fetch_url(url)
    parsed = urlparse(safe_url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a hostname")

    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None
    if literal is not None:
        if _ip_blocked(literal):
            raise ValueError("Blocked IP address")
        return SafeHttpsTarget(
            hostname=hostname, ip=str(literal), path_with_query=_path_with_query(parsed)
        )

    ips = _resolve_host_ips(hostname)
    if not ips:
        raise ValueError("Hostname could not be resolved")
    for ip in ips:
        if _ip_blocked(ip):
            raise ValueError("Hostname resolves to blocked IP address") from None
    # Prefer IPv4 for the pinned connection (broader compatibility).
    pinned = next((ip for ip in ips if ip.version == 4), ips[0])
    return SafeHttpsTarget(
        hostname=hostname, ip=str(pinned), path_with_query=_path_with_query(parsed)
    )


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
