# src/vfa/services/slot_service.py
from __future__ import annotations
import re
from typing import Any, Dict, Optional

ALLOWED_INSTALLMENTS = {3, 6, 12, 24, 36}

CITY_ALIASES = {
    "istanbul": "İstanbul",
    "ankara": "Ankara",
    "izmir": "İzmir",
    # istersen genişletirsin
}

def _extract_installment(text: str) -> Optional[int]:
    t = text.lower()

    # 1) "3 taksit" / "3 ay"
    m = re.search(r"\b(\d{1,2})\s*(taksit|ay)\b", t)
    if not m:
        # 2) "taksit 3"
        m = re.search(r"\b(taksit|ay)\s*(\d{1,2})\b", t)

    if not m:
        return None

    # gruplardan sayıyı al
    num = None
    for g in m.groups():
        if g and g.isdigit():
            num = int(g)
            break

    if num in ALLOWED_INSTALLMENTS:
        return num
    return None

def _extract_city(text: str) -> Optional[str]:
    t = text.lower()
    for key, pretty in CITY_ALIASES.items():
        # ankara, ankaradan, ankara'dan, ankaraya...
        if re.search(rf"\b{re.escape(key)}\w*\b", t):
            return pretty
    return None

def extract_slots(message: str) -> Dict[str, Any]:
    return {
        "installment": _extract_installment(message),
        "city": _extract_city(message),
        # msisdn (opsiyonel) istersen ekle:
        # "msisdn": _extract_msisdn(message),
    }