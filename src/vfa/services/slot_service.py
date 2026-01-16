from __future__ import annotations
import re
from typing import Optional, Dict

TR_CITIES = ["istanbul", "ankara", "izmir", "bursa", "antalya"]  # istersen genişlet

def extract_installment(text: str) -> Optional[int]:
    m = re.search(r"\b(12|24|36)\s*(ay|taksit)?\b", text.lower())
    return int(m.group(1)) if m else None

def extract_city(text: str) -> Optional[str]:
    t = text.lower()
    for c in TR_CITIES:
        if re.search(rf"\b{re.escape(c)}\b", t):
            return c.title()
    return None

def extract_slots(text: str) -> Dict[str, Optional[object]]:
    return {
        "installment": extract_installment(text),
        "city": extract_city(text),
    }
