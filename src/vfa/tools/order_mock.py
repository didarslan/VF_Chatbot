from __future__ import annotations

import uuid
from typing import Dict, Any, Optional
from vfa.core.schemas import OrderCreateResponse

_ORDERS: Dict[str, Dict[str, Any]] = {}

def create_order(msisdn: str, product_url: str, product_name: str, installment_months: Optional[int]) -> OrderCreateResponse:
    order_id = str(uuid.uuid4())
    _ORDERS[order_id] = {
        "order_id": order_id,
        "status": "CREATED",
        "msisdn": msisdn,
        "product_url": product_url,
        "product_name": product_name,
        "installment_months": installment_months,
    }
    return OrderCreateResponse(order_id=order_id, status="CREATED", message="Sipariş oluşturuldu (mock).")

def get_order_status(order_id: str) -> Dict[str, Any]:
    return _ORDERS.get(order_id, {"ok": False, "error": "ORDER_NOT_FOUND"})

def cancel_order(order_id: str) -> Dict[str, Any]:
    if order_id not in _ORDERS:
        return {"ok": False, "error": "ORDER_NOT_FOUND"}
    _ORDERS[order_id]["status"] = "CANCELLED"
    return {"ok": True, "order_id": order_id, "status": "CANCELLED"}
