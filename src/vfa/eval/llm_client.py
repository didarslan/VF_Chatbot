import hashlib
import json
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# openai>=1.x
try:
    from openai import OpenAI
    from openai import RateLimitError, APIError, APITimeoutError
except Exception:  # openai not installed
    OpenAI = None
    RateLimitError = Exception
    APIError = Exception
    APITimeoutError = Exception


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


class RateLimiter:
    """
    Basit pacing: her LLM çağrısı arasında en az min_interval kadar bekle.
    """
    def __init__(self, rpm: int):
        self.rpm = max(1, rpm)
        self.min_interval = 60.0 / float(self.rpm)
        self._last_call = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delta = now - self._last_call
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last_call = time.monotonic()


class OpenAIJsonCaller:
    """
    JSON output döndüren LLM caller:
    - Rate limiting (RPM)
    - Retry + exponential backoff (429/timeouts)
    - Disk cache
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
        self.timeout_s = _env_int("JUDGE_TIMEOUT_S", 30)
        self.max_retries = _env_int("JUDGE_MAX_RETRIES", 6)
        self.backoff_base = _env_float("JUDGE_BACKOFF_BASE", 1.5)  # seconds
        self.backoff_max = _env_float("JUDGE_BACKOFF_MAX", 30.0)
        self.rpm = _env_int("JUDGE_RPM", 20)  # güvenli default
        self.temperature = _env_float("JUDGE_TEMPERATURE", 0.0)
        self.max_output_tokens = _env_int("JUDGE_MAX_OUTPUT_TOKENS", 350)

        cache_dir = os.getenv("JUDGE_CACHE_DIR", str(Path("src/vfa/eval/.judge_cache")))
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.limiter = RateLimiter(self.rpm)

        if OpenAI is None or not self.api_key:
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)

    def _cache_key(self, system: str, user: str, model: str) -> str:
        h = hashlib.sha256()
        h.update(model.encode("utf-8"))
        h.update(b"\n---SYS---\n")
        h.update(system.encode("utf-8"))
        h.update(b"\n---USR---\n")
        h.update(user.encode("utf-8"))
        return h.hexdigest()

    def _cache_paths(self, key: str) -> Tuple[Path, Path]:
        return (self.cache_dir / f"{key}.json", self.cache_dir / f"{key}.txt")

    def _read_cache(self, key: str) -> Optional[Dict[str, Any]]:
        p_json, _ = self._cache_paths(key)
        if p_json.exists():
            try:
                return json.loads(p_json.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def _write_cache(self, key: str, obj: Dict[str, Any], raw_text: str) -> None:
        p_json, p_txt = self._cache_paths(key)
        try:
            p_json.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
            p_txt.write_text(raw_text, encoding="utf-8")
        except Exception:
            pass

    def _extract_text(self, resp: Any) -> str:
        # responses API
        if hasattr(resp, "output_text") and isinstance(resp.output_text, str):
            return resp.output_text

        # chat.completions API fallback
        try:
            return resp.choices[0].message.content
        except Exception:
            pass

        # dict fallback
        try:
            return str(resp)
        except Exception:
            return ""

    def call_json(self, system: str, user: str, model: Optional[str] = None) -> Dict[str, Any]:
        if self.client is None:
            return {"skipped": True, "reason": "openai_not_configured_or_missing_OPENAI_API_KEY"}

        model = model or self.model

        key = self._cache_key(system, user, model)
        cached = self._read_cache(key)
        if cached is not None:
            cached["_cached"] = True
            return cached

        # pacing
        self.limiter.wait()

        last_err = None
        for attempt in range(self.max_retries + 1):
            try:
                # prefer Responses API (openai>=1.x)
                resp = self.client.responses.create(
                    model=model,
                    input=[
                        {"role": "system", "content": [{"type": "input_text", "text": system}]},
                        {"role": "user", "content": [{"type": "input_text", "text": user}]},
                    ],
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens,
                    timeout=self.timeout_s,
                )
                text = self._extract_text(resp).strip()

                # JSON parse (modelden JSON istiyoruz)
                obj = json.loads(text)
                self._write_cache(key, obj, text)
                return obj

            except RateLimitError as e:
                last_err = e
                # exponential backoff + jitter
                wait = min(self.backoff_max, self.backoff_base * (2 ** attempt))
                wait = wait + random.uniform(0, 0.5)
                time.sleep(wait)
                # retry

            except APITimeoutError as e:
                last_err = e
                wait = min(self.backoff_max, self.backoff_base * (2 ** attempt))
                wait = wait + random.uniform(0, 0.5)
                time.sleep(wait)

            except APIError as e:
                last_err = e
                # bazı 5xx/connection issue'larda retry mantıklı
                wait = min(self.backoff_max, self.backoff_base * (2 ** attempt))
                wait = wait + random.uniform(0, 0.5)
                time.sleep(wait)

            except json.JSONDecodeError as e:
                # model JSON döndürmediyse: cache yazma, retry et (promptu daha sıkı yapacağız rubics tarafında)
                last_err = e
                wait = min(self.backoff_max, 1.0 + attempt)
                time.sleep(wait)

            except Exception as e:
                last_err = e
                break

        return {"skipped": True, "reason": f"judge_failed: {type(last_err).__name__}: {last_err}"}
