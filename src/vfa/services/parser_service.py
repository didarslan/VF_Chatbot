from bs4 import BeautifulSoup
import html2text

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    h = html2text.HTML2Text()
    h.ignore_images = True
    h.ignore_links = False
    text = h.handle(str(soup))
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)
