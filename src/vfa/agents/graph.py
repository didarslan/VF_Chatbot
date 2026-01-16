from __future__ import annotations

from langgraph.graph import StateGraph, END

from vfa.agents.nodes import (
    GraphState, classify_intent, route,
    knowledge_node, device_node, order_node, other_node, finalize
)
from vfa.services.tracing_service import TraceCollector
from vfa.services.rag_service import RAGService
from vfa.agents.knowledge_agent import KnowledgeAgent
from vfa.agents.device_agent import DeviceAgent
from vfa.agents.order_agent import OrderAgent


def build_graph():
    trace = TraceCollector()
    rag = RAGService()
    knowledge = KnowledgeAgent(rag)
    device = DeviceAgent()
    order = OrderAgent()

    g = StateGraph(GraphState)

    g.add_node("classify", lambda s: classify_intent(s))
    g.add_node("knowledge", lambda s: knowledge_node(s, knowledge, trace))
    g.add_node("device", lambda s: device_node(s, device, trace))
    g.add_node("order", lambda s: order_node(s, order, device, trace))
    g.add_node("other", lambda s: other_node(s))
    g.add_node("finalize", lambda s: finalize(s, trace))

    g.set_entry_point("classify")

    g.add_conditional_edges("classify", route, {
        "knowledge": "knowledge",
        "device": "device",
        "order": "order",
        "other": "other",
        "final": "finalize",
    })

    g.add_edge("knowledge", "finalize")
    g.add_edge("device", "finalize")
    g.add_edge("order", "finalize")
    g.add_edge("other", "finalize")
    g.add_edge("finalize", END)

    return g.compile()
