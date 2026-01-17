from __future__ import annotations
import re
from typing import List, Optional, Dict

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from vfa.core.schemas import ProductSummary
from vfa.core.prompts import DEVICE_SYSTEM
from vfa.services.scraper_service import fetch_html
from vfa.services.parser_service import html_to_text
from vfa.services.llm_factory import make_chat_llm, paced_invoke


class _ExtractedProduct(BaseModel):
    name: str = Field(..., description="Ürün adı")
    price_text: str = Field("", description="Fiyat / ödeme metni")
    installment_text: str = Field("", description="Taksit metni")
    highlights: List[str] = Field(default_factory=list, description="Öne çıkanlar")
    is_5g: Optional[bool] = Field(None, description="5G sinyali")


_llm = make_chat_llm(temperature=0.2)


def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[^\w\s]", "", s)  # noktalama temizle
    return s


def find_device_url_in_candidates(model_text: str, candidates: List[Dict[str, str]]) -> Optional[str]:
    mt = _norm(model_text)
    for c in candidates:
        name = _norm(c.get("name", "") or c.get("title", ""))
        if name and name in mt:
            return c.get("url")
    return None


def discover_product_urls(catalog_url: str, limit: int = 50) -> List[str]:
    html = fetch_html(catalog_url)
    soup = BeautifulSoup(html, "html.parser")
    urls: List[str] = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/faturaya-ek/" in href and "/p/telefonlar" in href:
            if href.startswith("/"):
                href = "https://www.vodafone.com.tr" + href
            if href not in urls:
                urls.append(href)
        if len(urls) >= limit:
            break

    return urls


def _heuristic_is_5g(text: str) -> Optional[bool]:
    t = text.lower()
    if "5g" in t:
        return True
    return None


def get_product_summary(product_url: str) -> ProductSummary:
    html = fetch_html(product_url)
    text = html_to_text(html)

    # structured extraction (clean + controllable)
    structured = _llm.with_structured_output(_ExtractedProduct)
    prompt = f"""{DEVICE_SYSTEM}

Sayfa metni (kısaltılmış):
{text[:14000]}

Yapılandırılmış ürün özetini çıkar."""

    p: _ExtractedProduct = paced_invoke(structured, prompt)

    if p.is_5g is None:
        p.is_5g = _heuristic_is_5g(text)

    return ProductSummary(
        name=p.name,
        source_url=product_url,
        is_5g=p.is_5g,
        price_text=p.price_text,
        installment_text=p.installment_text,
        highlights=p.highlights,
    )


def compare_products(url_a: str, url_b: str) -> dict:
    a = get_product_summary(url_a)
    b = get_product_summary(url_b)
    return {"a": a.model_dump(), "b": b.model_dump()}
