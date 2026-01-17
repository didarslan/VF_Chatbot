import os
import time
import random
import threading
from typing import Optional

from langchain_openai import ChatOpenAI

# OpenAI error types (safe import)
try:
    from openai import RateLimitError, APIError, APITimeoutError
except Exception:
    RateLimitError = Exception
    APIError = Exception
    APITimeoutError = Exception

# --- Global lock: process içinde aynı anda tek LLM çağrısı ---
_GLOBAL_LLM_LOCK = threading.Lock()
_LAST_CALL_TS = 0.0


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def _rate_limit_wait_locked():
    """
    Global pacing: her LLM çağrısı arası en az (60/RPM) saniye.
    Bu fonksiyon lock altında çağrılmalı.
    """
    global _LAST_CALL_TS
    rpm = max(1, _env_int("LLM_RPM", 10))  # default'u düşük tut
    min_interval = 60.0 / float(rpm)

    now = time.monotonic()
    delta = now - _LAST_CALL_TS
    if delta < min_interval:
        time.sleep(min_interval - delta)

    # jitter burst azaltır
    time.sleep(random.uniform(0, 0.25))
    _LAST_CALL_TS = time.monotonic()


def make_chat_llm(model: Optional[str] = None, temperature: float = 0.2) -> ChatOpenAI:
    """
    ChatOpenAI instance.
    Not: Asıl retry/backoff'u paced_invoke içinde biz yapacağız.
    O yüzden max_retries'i 0/1 gibi düşük tutmak daha stabil.
    """
    model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
    timeout_s = _env_float("LLM_TIMEOUT_S", 60.0)
    max_tokens = _env_int("LLM_MAX_TOKENS", 350)

    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        request_timeout=timeout_s,
        max_retries=0,     # ✅ retry'ı biz yönetiyoruz
        max_tokens=max_tokens,
    )
    return llm


def paced_invoke(runnable, inp):
    """
    Tüm LLM çağrılarını bunun üzerinden geçir:
    - Global lock (tek seferde 1 çağrı)
    - RPM pacing
    - 429/timeout/5xx için exponential backoff + retry
    """
    max_retries = _env_int("LLM_MAX_RETRIES", 8)
    backoff_base = _env_float("LLM_BACKOFF_BASE", 1.5)
    backoff_max = _env_float("LLM_BACKOFF_MAX", 30.0)

    last_err = None

    for attempt in range(max_retries + 1):
        try:
            # ✅ aynı anda tek çağrı + pacing
            with _GLOBAL_LLM_LOCK:
                _rate_limit_wait_locked()
                return runnable.invoke(inp)

        except RateLimitError as e:
            last_err = e
            wait = min(backoff_max, backoff_base * (2 ** attempt)) + random.uniform(0, 0.7)
            time.sleep(wait)

        except APITimeoutError as e:
            last_err = e
            wait = min(backoff_max, backoff_base * (2 ** attempt)) + random.uniform(0, 0.7)
            time.sleep(wait)

        except APIError as e:
            last_err = e
            wait = min(backoff_max, backoff_base * (2 ** attempt)) + random.uniform(0, 0.7)
            time.sleep(wait)

        except Exception as e:
            # Başka bir hata: retry etmeyi burada kesmek daha doğru
            last_err = e
            break

    raise RuntimeError(f"LLM call failed after retries: {type(last_err).__name__}: {last_err}")
