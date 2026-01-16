from __future__ import annotations

import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from vfa.core.config import settings

_last_ts = 0.0

def _rate_limit() -> None:
    global _last_ts
    min_interval = 1.0 / max(settings.http_rate_limit_rps, 0.1)
    now = time.time()
    sleep_s = (_last_ts + min_interval) - now
    if sleep_s > 0:
        time.sleep(sleep_s)
    _last_ts = time.time()


@retry(stop=stop_after_attempt(settings.http_max_retries), wait=wait_exponential(min=1, max=8))
def fetch_html(url: str) -> str:
    _rate_limit()
    r = requests.get(url, headers={"User-Agent": settings.user_agent}, timeout=settings.http_timeout_s)
    r.raise_for_status()
    return r.text
