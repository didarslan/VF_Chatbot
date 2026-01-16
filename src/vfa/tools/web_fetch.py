from __future__ import annotations

from vfa.services.scraper_service import fetch_html
from vfa.services.parser_service import html_to_text

def fetch_text(url: str) -> str:
    html = fetch_html(url)
    return html_to_text(html)
