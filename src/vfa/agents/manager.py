from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from vfa.services.intent_service import analyze_intent
from vfa.services.state_store import get_state, set_state
from vfa.services.slot_service import extract_slots
from vfa.services.vector_store_factory import get_vectorstore
from vfa.tools.phone_catalog import find_device_url_in_candidates

from vfa.agents.device_agent import DeviceAgent
from vfa.agents.knowledge_agent import KnowledgeAgent
from vfa.agents.order_agent import OrderAgent


class ChatResponse(BaseModel):
    answer: str
    actions: List[Dict[str, Any]] = []
    state: Dict[str, Any] = {}
    debug: Optional[Dict[str, Any]] = None


class ManagerAgent:
    """
    High-level orchestrator:
    - Intent + Slot + State based routing
    - Prevents repeated candidate listing
    - Runs: KnowledgeAgent (RAG), DeviceAgent (catalog), OrderAgent (mock order + optional sms)
    """

    def __init__(self):
        self.device_agent = DeviceAgent()
        vectorstore = get_vectorstore()
        self.knowledge_agent = KnowledgeAgent(rag=vectorstore)
        self.order_agent = OrderAgent()

    def handle(self, thread_id: str, message: str) -> ChatResponse:
        st = get_state(thread_id)

        # 1) Slot update (user can provide these at any time)
        slots = extract_slots(message)
        updates: Dict[str, Any] = {}
        if slots.get("installment"):
            updates["installment"] = slots["installment"]
        if slots.get("city"):
            updates["city"] = slots["city"]
        if slots.get("msisdn"):
            updates["msisdn"] = slots["msisdn"]

        if updates:
            st = set_state(thread_id, **updates)

        # 2) Intent analysis (LLM / heuristic)
        intent = analyze_intent(message)

        # 3) State-aware intent override (fix repeated listing issue)
        msg_l = message.lower()
        orderish = any(k in msg_l for k in ["almak istiyorum", "satın", "sipariş", "faturaya ek", "order", "sepete"])
        matched_url: Optional[str] = None

        if st.get("last_candidates"):
            matched_url = find_device_url_in_candidates(message, st.get("last_candidates", []))

        # Eğer agent discovery döndürüyor ama aslında kullanıcı seçim yapıyorsa override et
        if intent.intent == "DEVICE_DISCOVERY" and (matched_url or orderish):
            intent.intent = "DEVICE_SELECTION"
            intent.selected_model = intent.selected_model or message

        # Ayrıca LLM "OTHER" dese bile, aday listesi varken model seçimi varsa selection'a çek
        if intent.intent in ["OTHER", "UNKNOWN", "GENERAL"] and (matched_url or orderish) and st.get("last_candidates"):
            intent.intent = "DEVICE_SELECTION"
            intent.selected_model = intent.selected_model or message

        # 4) Routing
        if intent.intent == "KNOWLEDGE_5G":
            ans = self.knowledge_agent.answer(message, thread_id)
            return ChatResponse(
                answer=ans,
                actions=[{"type": "ANSWER_5G"}],
                state=st,
                debug={"intent": intent.model_dump()},
            )

        if intent.intent == "DEVICE_DISCOVERY":
            result = self.device_agent.suggest_5g_phones(message, thread_id)
            st = set_state(thread_id, stage="DISCOVERY", last_candidates=result.get("candidates", []))
            return ChatResponse(
                answer=result["answer"],
                actions=[{"type": "SHOW_CANDIDATES", "count": len(st.get("last_candidates", []))}],
                state=st,
                debug={"intent": intent.model_dump()},
            )

        if intent.intent in ["DEVICE_SELECTION", "ORDER_CREATE"]:
            model = intent.selected_model or message

            # URL resolution priority: existing selected_url -> matched_url from message -> candidates lookup
            url = st.get("selected_url") or matched_url
            if not url:
                url = find_device_url_in_candidates(model, st.get("last_candidates", []))

            # URL bulunamadıysa tekrar discovery'ye dön (ama aynı listeyi basmak yerine yönlendir)
            if not url:
                return ChatResponse(
                    answer=(
                        "Seçtiğiniz modeli katalog listesinde netleştiremedim.\n"
                        "Lütfen listeden model adını aynen yazar mısınız? (Örn: “Samsung Galaxy S25 FE 5G”)"
                    ),
                    actions=[{"type": "ASK_RESELECT"}],
                    state=st,
                    debug={"intent": intent.model_dump(), "note": "url_not_found"},
                )

            st = set_state(thread_id, stage="SELECTION", selected_model=model, selected_url=url)

            # Missing slots for order
            missing: List[str] = []
            if not st.get("installment"):
                missing.append("taksit (12/24/36)")
            if not st.get("city"):
                missing.append("teslimat ili")

            if missing:
                return ChatResponse(
                    answer=(
                        f"Seçiminizi aldım: **{model}**.\n"
                        f"Sipariş oluşturabilmem için eksik bilgiler var: {', '.join(missing)}.\n"
                        "Örn: `24 ay, İstanbul`"
                    ),
                    actions=[{"type": "ASK_SLOTS", "missing": missing, "selected_url": url}],
                    state=st,
                    debug={"intent": intent.model_dump()},
                )

            # All set -> create order
            order_res = self.order_agent.create_order(thread_id=thread_id, state=st)
            st = set_state(thread_id, stage="ORDER", last_order=order_res)

            return ChatResponse(
                answer=(
                    "Siparişiniz oluşturuldu ✅\n"
                    f"Order ID: **{order_res['order_id']}**\n"
                    f"Ürün: **{st.get('selected_model')}**\n"
                    f"Taksit: **{st.get('installment')} ay** | İl: **{st.get('city')}**"
                ),
                actions=[{"type": "CREATE_ORDER", "order_id": order_res["order_id"], "selected_url": st.get("selected_url")}],
                state=st,
                debug={"intent": intent.model_dump()},
            )

        # Default
        return ChatResponse(
            answer="Daha iyi yardımcı olabilmem için biraz daha detay paylaşır mısınız?",
            actions=[{"type": "ASK_CLARIFY"}],
            state=st,
            debug={"intent": intent.model_dump()},
        )
