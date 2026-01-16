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
from vfa.services.response_composer import ResponseComposer


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

    def __init__(self, composer: Optional[ResponseComposer] = None) -> None:
        self.device_agent = DeviceAgent()
        vectorstore = get_vectorstore()
        self.knowledge_agent = KnowledgeAgent(rag=vectorstore)
        self.order_agent = OrderAgent()
        self.response_composer = composer or ResponseComposer()
        

    def handle(self, thread_id: str, message: str) -> ChatResponse:
        st = get_state(thread_id)

        # 1) Slot update (user can provide these at any time)
        slots = extract_slots(message)

        has_slot = bool(slots.get("installment") or slots.get("city") or slots.get("msisdn"))
        slot_only = has_slot and len(message.strip()) <= 80 

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
        msg_l = message.strip().lower()
        if msg_l in {"merhaba","selam","selamlar","günaydın","iyi akşamlar","iyi geceler","hi","hello","hey"}:
            ans = self.response_composer.compose(
                intent="GREETING",
                action="GREET",
                data={"capabilities": ["5G soruları", "5G uyumlu telefon önerisi", "faturaya ek sipariş oluşturma"]}
            )
            return ChatResponse(answer=ans, actions=[{"type": "GREET"}], state=st, debug={"intent": intent.model_dump()})    

        # 3) State-aware intent override 
        msg_l = message.lower()
        orderish = any(k in msg_l for k in ["almak istiyorum", "satın", "sipariş", "faturaya ek", "order", "sepete"])
        matched_url = None

        if st.get("last_candidates"):
            matched_url = find_device_url_in_candidates(message, st.get("last_candidates", []))

        # ✅ Eğer kullanıcı sadece slot veriyorsa ve zaten seçili ürün varsa → ORDER_CREATE'a geç
        if has_slot and st.get("selected_url"):
            intent.intent = "ORDER_CREATE"

        # ✅ Discovery->Selection override sadece gerçekten model seçiyorsa çalışsın
        looks_like_model_pick = any(b in message.lower() for b in ["galaxy", "iphone", "xiaomi", "oppo", "huawei", "tecno", "infinix", "nubia", "realme", "vivo", "casper"])
        if intent.intent == "DEVICE_DISCOVERY" and st.get("last_candidates"):
            if (matched_url or orderish) and looks_like_model_pick:
                intent.intent = "DEVICE_SELECTION"
                intent.selected_model = intent.selected_model or message

        # 4) Routing
        if intent.intent == "ORDER_HOWTO":
            ans = self.response_composer.compose(
                intent="ORDER_HOWTO",
                action="EXPLAIN_ORDER_FLOW",
                data={
                    "steps": [
                        "Önce almak istediğiniz modeli seçiyoruz (isterseniz 5G uyumlu telefonları ben listeleyebilirim).",
                        "Sonra taksit süresi ve teslimat ilini alıyorum.",
                        "Bilgiler tamamlanınca siparişi oluşturup Order ID paylaşıyorum."
                    ],
                    "example": "Örn: “Tecno Spark Slim 5G almak istiyorum. Taksit yapmak istemiyorum. Ankara'dan teslim almak istiyorum.”"
                }
            )
            return ChatResponse(
                answer=ans,
                actions=[{"type": "HOWTO_ORDER"}],
                state=st,
                debug={"intent": intent.model_dump()},
            )

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
            model = intent.selected_model or st.get("selected_model") or message

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
            if intent.intent == "DEVICE_SELECTION" and not looks_like_model_pick and not orderish and not slot_only:
                return ChatResponse(
                    answer=(
                        f"Seçiminizi aldım: **{model}**.\n"
                        "Sipariş oluşturmak isterseniz lütfen belirtin."
                    ),
                    actions=[{"type": "CONFIRM_SELECTION", "selected_url": url}],
                    state=st,
                    debug={"intent": intent.model_dump()},
                )

            # Missing slots for order
            missing: List[str] = []
            if not st.get("installment"):
                missing.append("Taksit ister misiniz?")
            if not st.get("city"):
                missing.append("Teslimat ili")

            if missing:
                ans = self.composer.compose(
                    intent=intent.intent,
                    action="ASK_SLOTS",
                    data={
                        "selected_model": st.get("selected_model"),
                        "selected_url": st.get("selected_url"),
                        "missing": missing,
                        "example": "12 ay, Ankara"
                    }
                )
                return ChatResponse(
                    answer=ans,
                    actions=[{"type": "ASK_SLOTS", "missing": missing}],
                    state=st,
                    debug={"intent": intent.model_dump()}
                )

            # All set -> create order
            order_res = self.order_agent.create_order(thread_id=thread_id, state=st)
            st = set_state(thread_id, stage="ORDER", last_order=order_res)

            ans = self.composer.compose(
                intent="ORDER_CREATE",
                action="ORDER_CREATED",
                data={
                    "order_id": order_res["order_id"],
                    "selected_model": st.get("selected_model"),
                    "installment": st.get("installment"),
                    "city": st.get("city")
                }
            )
            return ChatResponse(
                answer=ans,
                actions=[{"type": "CREATE_ORDER", "order_id": order_res["order_id"]}],
                state=st,
                debug={"intent": intent.model_dump()}
            )

        # Default
        return ChatResponse(
            answer="Daha iyi yardımcı olabilmem için biraz daha detay paylaşır mısınız?",
            actions=[{"type": "ASK_CLARIFY"}],
            state=st,
            debug={"intent": intent.model_dump()},
        )
