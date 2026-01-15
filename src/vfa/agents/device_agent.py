from typing import List, Dict, Any
from vfa.tools import phone_catalog
from vfa.core.constants import CATALOG_URL

class DeviceAgent:
    def find_5g_phones(self, limit: int = 20) -> Dict[str, Any]:
        urls = phone_catalog.discover_product_urls(CATALOG_URL, limit=limit)
        items = []
        for u in urls:
            try:
                p = phone_catalog.lookup(u)
                if p.is_5g:
                    items.append(p.model_dump())
                if len(items) >= 5:
                    break
            except Exception:
                continue
        if not items:
            return {"items": [], "message": "Şu an 5G uyumlu cihazları tespit edemedim. Lütfen daha sonra tekrar deneyiniz."}
        return {"items": items, "message": "5G uyumlu olabilecek bazı cihazlar:"}

    def get_purchase_options(self, product_url: str) -> Dict[str, Any]:
        p = phone_catalog.lookup(product_url)
        return {"product": p.model_dump()}

    def compare(self, url_a: str, url_b: str) -> Dict[str, Any]:
        return phone_catalog.compare(url_a, url_b)
