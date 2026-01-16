from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class ProcessedDoc:
    text: str
    metadata: Dict[str, Any]
