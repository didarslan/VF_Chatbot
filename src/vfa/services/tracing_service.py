from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from vfa.core.schemas import ToolLog


class TraceCollector:
    """Thread-scope tool log collector (in-memory)."""
    def __init__(self):
        self.logs: List[ToolLog] = []

    def add(self, log: ToolLog) -> None:
        self.logs.append(log)

    def dump(self) -> List[ToolLog]:
        return list(self.logs)


@contextmanager
def tool_timer():
    start = time.time()
    yield lambda: int((time.time() - start) * 1000)
