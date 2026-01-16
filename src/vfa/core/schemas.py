from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

Intent = Literal["DEVICE", "KNOWLEDGE", "ORDER", "OTHER"]


class ProductSummary(BaseModel):
    name: str
    source_url: str
    is_5g: Optional[bool] = None
    price_text: str = ""
    installment_text: str = ""
    highlights: List[str] = Field(default_factory=list)


class ToolLog(BaseModel):
    tool: str
    allowed: bool = True
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: int = 0
    reason: str = ""


class ManagerResult(BaseModel):
    intent: Intent
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    tool_logs: List[ToolLog] = Field(default_factory=list)


class OrderCreateResponse(BaseModel):
    order_id: str
    status: str
    message: str


class SmsResponse(BaseModel):
    message_id: str
    delivery_status: str
