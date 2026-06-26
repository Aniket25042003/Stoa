"""Optional robots.txt respect before fetching."""

from __future__ import annotations

import logging

import httpx

from stoa_core.security.ssrf import resolve_safe_https_target

logger = logging.getLogger(__name__)
USER_AGENT = "Stoa-Intel-Bot/0.1 (+https://stoa.ai)"


def is_path_allowed_by_robots(url: str, *, timeout: float = 8.0) -> bool:
    """Best-effort robots.txt check. Returns True if allowed or robots unavailable."""
    try:
        target = resolve_safe_https_target(url)
        pinned_host = f"[{target.ip}]" if ":" in target.ip else target.ip
        pinned_url = f"https://{pinned_host}/robots.txt"
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            resp = client.get(
                pinned_url,
                headers={"Host": target.hostname, "User-Agent": USER_AGENT},
                extensions={"sni_hostname": target.hostname},
            )
            if resp.status_code >= 400:
                return True
            body = resp.text.lower()
            if "disallow: /" in body and "allow:" not in body:
                return False
    except Exception as exc:
        logger.debug("robots.txt check skipped for %s: %s", url, exc)
    return True
