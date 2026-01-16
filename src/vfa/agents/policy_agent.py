from __future__ import annotations

from typing import Dict, List
from vfa.core.schemas import Intent

class PolicyAgent:
    """Allow-list policy: intent -> allowed tools."""
    _POLICY: Dict[Intent, List[str]] = {
        "KNOWLEDGE": ["rag.answer"],
        "DEVICE": ["phone_catalog.discover", "phone_catalog.summary", "phone_catalog.compare"],
        "ORDER": ["order.create", "sms.send"],
        "OTHER": [],
    }

    def allowed_tools(self, intent: Intent) -> List[str]:
        return self._POLICY.get(intent, [])
