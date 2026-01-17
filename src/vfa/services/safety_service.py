from __future__ import annotations

import re
from urllib.parse import urlparse
from vfa.core.constants import ALLOWED_DOMAINS

_MSISDN_RE = re.compile(r"\b(90)?5\d{9}\b")

def mask_msisdn(text: str) -> str:
    return _MSISDN_RE.sub("5*********", text)

def is_allowed_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc
        return host in ALLOWED_DOMAINS
    except Exception:
        return False

def looks_like_prompt_injection(text: str) -> bool:
    t = text.lower()
    bad = ["ignore previous", "system prompt", "developer message", "jailbreak", "tool output"]
    return any(x in t for x in bad)

def looks_like_sensitive_request(text: str) -> bool:
    t = text.lower()
    patterns = [
        "tc kimlik",
        "kimlik numaras",
        "tüm kullanıcı verileri",
        "tum kullanici verileri",
        "kullanıcı verilerini dök",
        "kullanici verilerini dok",
        "müşteri verisi",
        "musteri verisi",
        "verilerini dök",
        "verilerini dok",
    ]
    return any(p in t for p in patterns)
