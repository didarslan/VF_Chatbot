from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class RawPage:
    url: str
    html: str
    fetched_at_utc: datetime
    status_code: int = 200
    error: Optional[str] = None
