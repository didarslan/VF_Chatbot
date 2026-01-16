from .web_fetch import fetch_text
from .phone_catalog import discover_product_urls, get_product_summary, compare_products
from .order_mock import create_order, get_order_status, cancel_order
from .sms_mock import send_sms, send_otp

__all__ = [
    "fetch_text",
    "discover_product_urls", "get_product_summary", "compare_products",
    "create_order", "get_order_status", "cancel_order",
    "send_sms", "send_otp",
]
