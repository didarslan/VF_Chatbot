from typing import Dict, List
from vfa.core.schemas import Intent

class PolicyAgent:
    """
    Basit allow-list policy.
    Sonraki sprint: injection detection + role/segment + rate limit.
    """
    POLICY: Dict[Intent, Dict[str, List[str]]] = {
        "DEVICE": {
            "tools": ["phone_catalog.lookup", "phone_catalog.compare", "phone_catalog.discover_product_urls"],
            "agents": ["device_agent"],
        },
        "KNOWLEDGE": {"tools": ["rag.answer"], "agents": ["knowledge_agent"]},
        "ORDER": {"tools": ["order_mock.create_order", "sms_mock.send_sms", "sms_mock.send_otp"], "agents": ["order_agent"]},
        "OTHER": {"tools": [], "agents": []},
    }

    def allowed(self, intent: Intent) -> Dict[str, List[str]]:
        return self.POLICY.get(intent, self.POLICY["OTHER"])
