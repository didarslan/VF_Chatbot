from __future__ import annotations

from vfa.core.schemas import ManagerResult

def simple_auto_metrics(message: str, manager_result: ManagerResult) -> dict:
    """
    Minimum otomatik metrikler:
    - has_sources: knowledge cevaplarında kaynak link var mı?
    - dont_know_ok: "bilgi yoksa bilmiyorum" davranışı
    """
    ans = (manager_result.message or "").lower()
    has_sources = ("kaynaklar:" in ans) or ("https://www.vodafone.com.tr" in ans)

    # Bu metrik çok basit: Vodafone dışı konu sorulursa "bilmiyorum" dedi mi?
    # (dataset'te OUT_OF_SCOPE örnekleri koyarsan anlamlı olur)
    dont_know_ok = ("bilgi sahibi değilim" in ans) or (manager_result.intent != "KNOWLEDGE")

    return {"has_sources": bool(has_sources), "dont_know_ok": bool(dont_know_ok)}
