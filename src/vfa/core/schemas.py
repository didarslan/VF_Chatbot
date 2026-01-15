from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal

Intent = Literal["DEVICE", "KNOWLEDGE", "ORDER", "OTHER"]

class ProductSummary(BaseModel):
    name: str
    price_text: str = ""
    installment_text: str = ""
    is_5g: Optional[bool] = None
    highlights: List[str] = Field(default_factory=list)
    source_url: str

class OrderCreateResponse(BaseModel):
    order_id: str
    status: str
    message: str

class SmsResponse(BaseModel):
    message_id: str
    delivery_status: str

class ToolLog(BaseModel):
    tool: str
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    allowed: bool = True
    reason: str = ""
    latency_ms: int = 0

class ManagerResult(BaseModel):
    intent: Intent
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    tool_logs: List[ToolLog] = Field(default_factory=list)
class CatalogSearchResult(BaseModel):
    products: List[ProductSummary] = Field(default_factory=list)    