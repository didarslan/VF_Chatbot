from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from vfa.core.constants import SEED_URLS, CATALOG_URL
from vfa.services.scraper_service import fetch_html
from vfa.services.parser_service import html_to_text
from vfa.services.ingestion_service import make_document, chunk_documents
from vfa.services.vector_store_factory import get_vectorstore
from vfa.tools.phone_catalog import discover_product_urls


def main() -> None:
    vs = get_vectorstore()

    docs = []
    # Seed pages (5G/help + catalog)
    for url in SEED_URLS:
        try:
            html = fetch_html(url)
            text = html_to_text(html)
            docs.append(make_document(text, {"source_url": url, "doc_type": "seed"}))
            print("[OK] seed:", url)
        except Exception as e:
            print("[FAIL] seed:", url, "-", str(e))

    # Discover product pages from catalog (limit)
    try:
        product_urls = discover_product_urls(CATALOG_URL, limit=50)
        for u in product_urls:
            try:
                html = fetch_html(u)
                text = html_to_text(html)
                docs.append(make_document(text, {"source_url": u, "doc_type": "product"}))
                print("[OK] product:", u)
            except Exception as e:
                print("[FAIL] product:", u, "-", str(e))
    except Exception as e:
        print("[FAIL] catalog discovery:", str(e))

    chunks = chunk_documents(docs, chunk_size=1500, chunk_overlap=150)
    vs.add_documents(chunks)
    print(f"Indexed chunks: {len(chunks)}")


if __name__ == "__main__":
    main()
