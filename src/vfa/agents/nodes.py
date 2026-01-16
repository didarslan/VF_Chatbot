from __future__ import annotations

import re
from typing import TypedDict, Optional, List

from vfa.core.schemas import Intent, ToolLog
from vfa.services.safety_service import looks_like_prompt_injection, is_allowed_url, mask_msisdn
from vfa.services.tracing_service import tool_timer, TraceCollector
from vfa.agents.policy_agent import PolicyAgent
from vfa.agents.knowledge_agent import KnowledgeAgent
from vfa.agents.device_agent import DeviceAgent
from vfa.agents.order_agent import OrderAgent


_MSISDN_RE = re.compile(r"\b(90)?5\d{9}\b")
_URL_RE = re.compile(r"https?://\S+")

class GraphState(TypedDict, total=False):
    thread_id: str
    message: str
    intent: Intent
    msisdn: Optional[str]
    urls: List[str]
    installment: Optional[int]
    response: str
    data: dict
    tool_logs: List[ToolLog]

def classify_intent(state: GraphState) -> GraphState:
    msg = state["message"]
    if looks_like_prompt_injection(msg):
        state["intent"] = "OTHER"
        state["response"] = "Güvenlik nedeniyle bu isteği işleyemiyorum. Lütfen talebinizi yeniden iletir misiniz?"
        return state

    t = msg.lower()
    if any(k in t for k in ["sipariş", "satın al", "order", "faturaya ek"]):
        state["intent"] = "ORDER"
    elif any(k in t for k in ["5g uyumlu", "5g telefon", "telefon öner", "cihaz", "iphone", "samsung", "xiaomi", "oppo", "huawei", "karşılaştır"]):
        state["intent"] = "DEVICE"
    elif "5g" in t or "yardım" in t or "internet" in t:
        state["intent"] = "KNOWLEDGE"
    else:
        state["intent"] = "OTHER"

    state["urls"] = _URL_RE.findall(msg) or []
    ms = _MSISDN_RE.search(msg.replace(" ", ""))
    state["msisdn"] = ms.group(0) if ms else None

    m = re.search(r"(\d{1,2})\s*ay", t)
    state["installment"] = int(m.group(1)) if m else None

    state.setdefault("tool_logs", [])
    return state

def route(state: GraphState) -> str:
    if state.get("response"):
        return "final"
    return state["intent"].lower()

def knowledge_node(state: GraphState, knowledge: KnowledgeAgent, trace: TraceCollector) -> GraphState:
    with tool_timer() as t:
        out = knowledge.answer(state["message"])
        latency = t()
    trace.add(ToolLog(tool="rag.answer", input={"q": mask_msisdn(state["message"])}, output={"has_sources": bool(out.get("sources"))}, latency_ms=latency))
    msg = out["answer"]
    if out.get("sources"):
        msg += "\n\nKaynaklar:\n" + "\n".join(out["sources"][:4])
    state["response"] = msg
    state["data"] = out
    return state

def device_node(state: GraphState, device: DeviceAgent, trace: TraceCollector) -> GraphState:
    urls = state.get("urls") or []

    # compare
    if len(urls) >= 2:
        if not (is_allowed_url(urls[0]) and is_allowed_url(urls[1])):
            state["response"] = "Sadece Vodafone alan adındaki ürün linkleriyle işlem yapabilirim."
            return state
        with tool_timer() as t:
            out = device.compare(urls[0], urls[1])
            latency = t()
        trace.add(ToolLog(tool="phone_catalog.compare", input={"a": urls[0], "b": urls[1]}, output={"ok": True}, latency_ms=latency))
        state["response"] = "Karşılaştırma sonucu:"
        state["data"] = out
        return state

    # details
    if len(urls) == 1:
        if not is_allowed_url(urls[0]):
            state["response"] = "Sadece Vodafone alan adındaki ürün linkleriyle işlem yapabilirim."
            return state
        with tool_timer() as t:
            out = device.get_details(urls[0])
            latency = t()
        trace.add(ToolLog(tool="phone_catalog.summary", input={"url": urls[0]}, output={"ok": True}, latency_ms=latency))
        state["response"] = "Ürün detayları:"
        state["data"] = out
        return state

    # find 5g
    with tool_timer() as t:
        out = device.find_5g_candidates(limit=30, top_n=5)
        latency = t()
    trace.add(ToolLog(tool="phone_catalog.discover", input={"catalog": "faturaya-ek/telefonlar"}, output={"count": len(out.get("items", []))}, latency_ms=latency))

    items = out.get("items", [])
    if not items:
        state["response"] = "Şu an 5G uyumlu cihazları tespit edemedim. Lütfen daha sonra tekrar deneyiniz."
        state["data"] = out
        return state

    lines = []
    for it in items[:5]:
        lines.append(f"- {it.get('name')} (link: {it.get('source_url')})")
    state["response"] = "5G uyumlu olabilecek bazı cihazlar:\n" + "\n".join(lines)
    state["data"] = out
    return state

def order_node(state: GraphState, order: OrderAgent, device: DeviceAgent, trace: TraceCollector) -> GraphState:
    msisdn = state.get("msisdn")
    urls = state.get("urls") or []
    installment = state.get("installment")

    if not msisdn:
        state["response"] = "Sipariş oluşturabilmem için telefon numaranızı (5XXXXXXXXX) paylaşır mısınız?"
        return state

    if not urls:
        state["response"] = "Sipariş için Vodafone ürün linkini paylaşır mısınız?"
        return state

    if not is_allowed_url(urls[0]):
        state["response"] = "Sadece Vodafone alan adındaki ürün linkleriyle sipariş oluşturabilirim."
        return state

    if installment is None:
        state["response"] = "Kaç ay taksit istersiniz? (Örn: 6 ay / 12 ay)"
        return state

    # product name via device detail (reuse)
    with tool_timer() as t1:
        detail = device.get_details(urls[0])
        latency1 = t1()
    trace.add(ToolLog(tool="phone_catalog.summary", input={"url": urls[0]}, output={"ok": True}, latency_ms=latency1))

    product_name = detail["product"]["name"]

    with tool_timer() as t2:
        out = order.create_order_flow(msisdn=msisdn, product_url=urls[0], product_name=product_name, installment_months=installment)
        latency2 = t2()
    trace.add(ToolLog(tool="order.create", input={"msisdn": "masked", "months": installment}, output={"status": out["order"]["status"]}, latency_ms=latency2))

    state["response"] = "Siparişiniz oluşturuldu ve bilgilendirme SMS’i gönderildi (mock)."
    state["data"] = out
    return state

def other_node(state: GraphState) -> GraphState:
    state["response"] = "Bu konuda bilgi sahibi değilim. 5G, cihaz veya sipariş konularında yardımcı olabilirim."
    return state

def finalize(state: GraphState, trace: TraceCollector) -> GraphState:
    state["tool_logs"] = trace.dump()
    return state
