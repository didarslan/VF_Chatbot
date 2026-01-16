from __future__ import annotations
from typing import Dict, Any

_STATE: Dict[str, Dict[str, Any]] = {}

def get_state(thread_id: str) -> Dict[str, Any]:
    return _STATE.setdefault(thread_id, {
        "stage": "DISCOVERY",         # DISCOVERY | SELECTION | ORDER
        "selected_model": None,
        "selected_url": None,
        "installment": None,
        "city": None,
        "last_candidates": [],        # [{"name":..., "url":...}]
    })

def set_state(thread_id: str, **kwargs) -> Dict[str, Any]:
    st = get_state(thread_id)
    st.update(kwargs)
    return st

def reset_state(thread_id: str) -> Dict[str, Any]:
    _STATE.pop(thread_id, None)
    return get_state(thread_id)
