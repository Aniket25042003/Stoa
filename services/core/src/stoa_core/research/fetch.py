from __future__ import annotations

import logging
import re

import httpx

from stoa_core.research.robots import is_path_allowed_by_robots
from stoa_core.security.ssrf import resolve_safe_https_target

logger = logging.getLogger(__name__)

USER_AGENT = "Stoa-Intel-Bot/0.1 (+https://stoa.ai)"


def html_to_text(html: str, *, max_chars: int = 20000) -> str:
    if not html:
        return ""
    text = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</p>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def fetch_page_text(url: str, timeout: float = 15.0, *, as_text: bool = True) -> str:
    if not is_path_allowed_by_robots(url, timeout=min(timeout, 8.0)):
        logger.info("robots.txt disallows fetch for %s", url)
        return ""
    try:
        target = resolve_safe_https_target(url)
        pinned_host = f"[{target.ip}]" if ":" in target.ip else target.ip
        pinned_url = f"https://{pinned_host}{target.path_with_query}"
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            resp = client.get(
                pinned_url,
                headers={"Host": target.hostname, "User-Agent": USER_AGENT},
                extensions={"sni_hostname": target.hostname},
            )
            resp.raise_for_status()
            body = resp.text[:50000]
            return html_to_text(body) if as_text else body
    except Exception as exc:
        logger.warning("Fetch failed for %s: %s", url, exc)
        return ""
