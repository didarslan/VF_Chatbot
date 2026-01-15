import re
from vfa.core.schemas import ManagerResult, Intent, ToolLog
from vfa.core.logging import timer_ms
from vfa.services.safety_service import looks_like_prompt_injection, redact_msisdn
from vfa.agents.policy_agent import PolicyAgent
from vfa.agents.knowledge_agent import KnowledgeAgent
from vfa.agents.device_agent import DeviceAgent
from vfa.agents.order_agent import OrderAgent
from vfa.services.rag_service import RAGService

_MSISDN_RE = re.compile(r"\b(90)?5\d{9}\b")
_URL_RE = re.compile(r"https?://\S+")

class ManagerAgent:
    def __init__(self):
        self.policy = PolicyAgent()
        self.rag = RAGService()
        self.knowledge = KnowledgeAgent(self.rag)
        self.device = DeviceAgent()
        self.order = OrderAgent()

    def infer_intent(self, msg: str) -> Intent:
        t = msg.lower()
        if any(k in t for k in ["sipariş", "satın al", "faturaya ek", "order", "sepete"]):
            return "ORDER"
        if any(k in t for k in ["5g uyumlu", "5g telefon", "telefon öner", "cihaz öner", "iphone", "samsung", "xiaomi", "oppo", "huawei", "karşılaştır"]):
            return "DEVICE"
        if any(k in t for k in ["5g", "kapsama", "hız testi", "yardım", "sss", "internet"]):
            return "KNOWLEDGE"
        return "OTHER"

    def _extract_msisdn(self, msg: str):
        m = _MSISDN_RE.search(msg.replace(" ", ""))
        return m.group(0) if m else None

    def _extract_urls(self, msg: str):
        return _URL_RE.findall(msg)

    def _extract_installment(self, msg: str):
        # "12 ay", "12" gibi
        m = re.search(r"(\d{1,2})\s*ay", msg.lower())
        if m:
            return int(m.group(1))
        m2 = re.search(r"\b(3|6|9|12|18|24)\b", msg)
        return int(m2.group(1)) if m2 else None

    def handle(self, thread_id: str, message: str) -> ManagerResult:
        safe_msg = redact_msisdn(message)

        if looks_like_prompt_injection(message):
            return ManagerResult(
                intent="OTHER",
                message="Güvenlik nedeniyle bu isteği işleyemiyorum. Lütfen talebinizi Vodafone 5G veya cihaz/sipariş konularında yeniden iletir misiniz?"
            )

        intent = self.infer_intent(message)
        allow = self.policy.allowed(intent)

        logs: list[ToolLog] = []

        # DEVICE
        if intent == "DEVICE" and "device_agent" in allow["agents"]:
            urls = self._extract_urls(message)
            if len(urls) >= 2:
                with timer_ms() as t:
                    out = self.device.compare(urls[0], urls[1])
                    logs.append(ToolLog(tool="phone_catalog.compare", input={"a": urls[0], "b": urls[1]}, output={"ok": True}, latency_ms=t()))
                return ManagerResult(intent=intent, message="Karşılaştırma sonucu aşağıdadır.", data=out, tool_logs=logs)

            if len(urls) == 1:
                with timer_ms() as t:
                    out = self.device.get_purchase_options(urls[0])
                    logs.append(ToolLog(tool="phone_catalog.lookup", input={"url": urls[0]}, output={"ok": True}, latency_ms=t()))
                return ManagerResult(
                    intent=intent,
                    message="Ürün detaylarını ve satın alma bilgilerini aşağıda bulabilirsiniz.",
                    data=out,
                    tool_logs=logs
                )

            # "5G uyumlu telefon bul"
            with timer_ms() as t:
                out = self.device.find_5g_phones(limit=25)
                logs.append(ToolLog(tool="phone_catalog.discover_product_urls+lookup", input={"catalog": "faturaya-ek/telefonlar"}, output={"ok": True}, latency_ms=t()))
            return ManagerResult(intent=intent, message=out.get("message",""), data=out, tool_logs=logs)

        # KNOWLEDGE
        if intent == "KNOWLEDGE" and "knowledge_agent" in allow["agents"]:
            with timer_ms() as t:
                out = self.knowledge.answer(message)
                logs.append(ToolLog(tool="rag.answer", input={"q": safe_msg}, output={"ok": True}, latency_ms=t()))
            msg = out["answer"]
            if out.get("sources"):
                msg += "\n\nKaynaklar:\n" + "\n".join(out["sources"][:4])
            return ManagerResult(intent=intent, message=msg, data=out, tool_logs=logs)

        # ORDER
        if intent == "ORDER" and "order_agent" in allow["agents"]:
            msisdn = self._extract_msisdn(message)
            urls = self._extract_urls(message)
            installment = self._extract_installment(message)

            if not msisdn:
                return ManagerResult(intent=intent, message="Sipariş oluşturabilmem için telefon numaranızı (5XXXXXXXXX) paylaşır mısınız?")

            if not urls:
                return ManagerResult(intent=intent, message="Sipariş için ürün linkini paylaşır mısınız? (Vodafone ürün sayfası URL’si)")

            # ürün adını lookup ile çıkar
            from vfa.tools.phone_catalog import lookup
            with timer_ms() as t1:
                p = lookup(urls[0])
                logs.append(ToolLog(tool="phone_catalog.lookup", input={"url": urls[0]}, output={"ok": True}, latency_ms=t1()))

            if installment is None:
                return ManagerResult(intent=intent, message="Kaç ay taksit istersiniz? (Örn: 6 ay / 12 ay)")

            with timer_ms() as t2:
                out = self.order.create_order_flow(msisdn=msisdn, product_url=urls[0], product_name=p.name, installment_months=installment)
                logs.append(ToolLog(tool="order_mock.create_order+sms_mock.send_sms", input={"msisdn": "masked", "months": installment}, output={"ok": True}, latency_ms=t2()))

            return ManagerResult(intent=intent, message="Siparişiniz oluşturuldu ve bilgilendirme SMS’i gönderildi (mock).", data=out, tool_logs=logs)

        return ManagerResult(intent=intent, message="Bu konuda yardımcı olabilmem için talebinizi 5G, cihaz veya sipariş kapsamında biraz daha detaylandırır mısınız?")
