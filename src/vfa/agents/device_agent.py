from __future__ import annotations

from typing import Any, Dict, List, Optional

from vfa.core.constants import CATALOG_URL
from vfa.tools.phone_catalog import discover_product_urls, get_product_summary, compare_products


class DeviceAgent:
    """
    Device discovery & selection helper.
    - 5G uyumlu cihaz adaylarını bulur (catalog scrape)
    - Seçim adımında Manager'ın state'ine yazılabilecek candidate listesi üretir
    """

    def suggest_5g_phones(self, user_message: str, thread_id: str, top_n: int = 5, limit: int = 30) -> Dict[str, Any]:
        """
        Manager'ın DISCOVERY adımında çağıracağı ana fonksiyon.
        Return format:
        {
          "answer": "<Turkish message>",
          "candidates": [{"name": "...", "url": "..."}]
        }
        """
        candidates = self.find_5g_candidates(limit=limit, top_n=top_n, user_message=user_message)

        if not candidates:
            return {
                "answer": "Şu an katalogdan 5G uyumlu cihaz listesi çıkaramadım. İsterseniz marka veya bütçe paylaşır mısınız?",
                "candidates": [],
            }

        lines = ["5G uyumlu olabilecek bazı cihazlar:"]
        for c in candidates:
            lines.append(f"- {c['name']} (link: {c['url']})")

        lines.append("\nHangi modeli satın almak istersiniz? Örn: “Samsung Galaxy S25 FE 5G almak istiyorum”")
        return {"answer": "\n".join(lines), "candidates": candidates}

    def find_5g_candidates(self, limit: int = 30, top_n: int = 5, user_message: str = "") -> List[Dict[str, str]]:
        """
        Katalogdan ürün URL'leri keşfeder, 5G olanları seçer.
        Basit bir 'marka filtresi' uygular (kullanıcı mesajında samsung/iphone vs geçerse).
        """
        brand_hint = self._extract_brand_hint(user_message)

        urls = discover_product_urls(CATALOG_URL, limit=limit)
        out: List[Dict[str, str]] = []

        for u in urls:
            try:
                p = get_product_summary(u)

                # Bazı ürünlerde alan isimleri farklı olabilir -> robust davran
                name = getattr(p, "name", None) or getattr(p, "product_name", None) or getattr(p, "title", None) or "Bilinmeyen Model"
                is_5g = bool(getattr(p, "is_5g", False))

                if not is_5g:
                    continue

                if brand_hint and brand_hint not in name.lower():
                    continue

                out.append({"name": str(name), "url": str(u)})

                if len(out) >= top_n:
                    break
            except Exception:
                continue

        return out

    def get_details(self, product_url: str) -> Dict[str, Any]:
        p = get_product_summary(product_url)
        return {"product": p.model_dump()}

    def compare(self, url_a: str, url_b: str) -> Dict[str, Any]:
        return compare_products(url_a, url_b)

    @staticmethod
    def _extract_brand_hint(text: str) -> Optional[str]:
        t = (text or "").lower()
        for b in ["samsung", "iphone", "xiaomi", "oppo", "huawei", "realme", "vivo", "tecno", "infinix", "nubia", "casper"]:
            if b in t:
                return b
        return None
