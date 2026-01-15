import re
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from vfa.core.config import settings
from vfa.core.schemas import ProductSummary
from vfa.core.prompts import DEVICE_SYSTEM
from vfa.services.scraper_service import fetch_html
from vfa.services.parser_service import html_to_text

class _ExtractedProduct(BaseModel):
    name: str = Field(..., description="Ürün adı")
    price_text: str = Field("", description="Fiyat veya ödeme bilgisi metni")
    installment_text: str = Field("", description="Taksit bilgisi metni")
    highlights: List[str] = Field(default_factory=list, description="Öne çıkanlar")
    is_5g: Optional[bool] = Field(None, description="5G uyum sinyali")

_llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    temperature=0.0,
    use_responses_api=True,
    output_version="responses/v1",
)

def discover_product_urls(catalog_url: str, limit: int = 50) -> List[str]:
    html = fetch_html(catalog_url)
    soup = BeautifulSoup(html, "html.parser")
    urls = []
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

def lookup(url: str) -> ProductSummary:
    html = fetch_html(url)
    text = html_to_text(html)

    structured = _llm.with_structured_output(_ExtractedProduct)
    prompt = f"""{DEVICE_SYSTEM}

Sayfa metni (kısaltılmış):
{text[:16000]}

Yapılandırılmış ürün özetini çıkar."""
    p: _ExtractedProduct = structured.invoke(prompt)

    # Heuristic fallback for 5G
    if p.is_5g is None:
        p.is_5g = _heuristic_is_5g(text)

    return ProductSummary(
        name=p.name,
        price_text=p.price_text,
        installment_text=p.installment_text,
        highlights=p.highlights,
        is_5g=p.is_5g,
        source_url=url,
    )

def compare(url_a: str, url_b: str) -> dict:
    a = lookup(url_a)
    b = lookup(url_b)
    return {"a": a.model_dump(), "b": b.model_dump()}

def extract_price_number(price_text: str) -> Optional[float]:
    # çok basit: 12.345,67 gibi TR format
    m = re.search(r"(\d{1,3}(\.\d{3})*(,\d{2})?)", price_text)
    if not m:
        return None
    s = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(s)
    except:
        return None
