import re

def redact_msisdn(text: str) -> str:
    # basit maskeleme: 90 ile başlayan 10-12 haneler
    return re.sub(r"\b(90)?5\d{9}\b", "5*********", text)

def looks_like_prompt_injection(text: str) -> bool:
    t = text.lower()
    risky = ["ignore previous", "system prompt", "developer message", "tool output", "jailbreak"]
    return any(x in t for x in risky)
