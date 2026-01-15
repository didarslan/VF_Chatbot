"""
Index builder:
- Seed URL’leri indirir
- Text -> Document
- Chunk
- Vector store’a ekler (Milvus/Zilliz veya Chroma)
"""
from vfa.core.constants import SEED_URLS, CATALOG_URL
from vfa.services.scraper_service import fetch_html
from vfa.services.parser_service import html_to_text
from vfa.services.ingestion_service import make_document, chunk_documents
from vfa.services.vector_store_factory import get_vectorstore
from vfa.tools.phone_catalog import discover_product_urls

def main():
    vs = get_vectorstore()

    docs = []
    for url in SEED_URLS:
        try:
            html = fetch_html(url)
            text = html_to_text(html)
            docs.append(make_document(text, {"source_url": url, "type": "seed"}))
            print("Seed ok:", url)
        except Exception as e:
            print("Seed fail:", url, e)

    # katalogdan ürün keşfi (limitli)
    try:
        product_urls = discover_product_urls(CATALOG_URL, limit=40)
        for u in product_urls:
            try:
                html = fetch_html(u)
                text = html_to_text(html)
                docs.append(make_document(text, {"source_url": u, "type": "product"}))
                print("Product ok:", u)
            except Exception as e:
                print("Product fail:", u, e)
    except Exception as e:
        print("Catalog discovery fail:", e)

    chunks = chunk_documents(docs, chunk_size=1500, chunk_overlap=150)
    vs.add_documents(chunks)
    print(f"Indexed chunks: {len(chunks)}")

if __name__ == "__main__":
    main()
