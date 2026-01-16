from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IndexBuildInfo:
    backend: str
    collection: str
    total_chunks: int
    built_at_utc: datetime
