import os
import json
import requests
import streamlit as st

st.set_page_config(page_title="Vodafone Agentic Assistant", layout="wide")

DEFAULT_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_ENDPOINT = os.getenv("API_CHAT_ENDPOINT", "/chat")

st.title("📱 Vodafone Agentic Assistant")
st.caption("FastAPI agent server'ına bağlanır: soru sor → cevap al")

with st.sidebar:
    st.header("Ayarlar")
    base_url = st.text_input("API Base URL", value=DEFAULT_BASE_URL)
    endpoint = st.text_input("Chat Endpoint", value=DEFAULT_ENDPOINT)
    timeout_s = st.number_input("Timeout (sn)", min_value=5, max_value=120, value=30, step=5)
    thread_id = st.text_input("thread_id (opsiyonel)", value="ui_thread_1")
    show_raw = st.checkbox("Ham JSON cevabı göster", value=False)

    st.divider()
    st.markdown("**Hızlı Kontrol**")
    if st.button("Docs'u aç"):
        st.write(f"{base_url}/docs")

api_url = f"{base_url.rstrip('/')}{endpoint}"

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role": "user"/"assistant", "content": "..."}]

# Render history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

def extract_answer(payload: dict) -> str:
    """
    Backend farklı alan adları döndürebilir diye dayanıklı parse.
    """
    for key in ["answer", "response", "message", "output", "result", "text"]:
        if key in payload and isinstance(payload[key], str) and payload[key].strip():
            return payload[key]
    # Bazı sistemler {"data": {"answer": "..."}}
    if "data" in payload and isinstance(payload["data"], dict):
        return extract_answer(payload["data"])
    return json.dumps(payload, ensure_ascii=False, indent=2)

user_text = st.chat_input("Sorunu yaz (örn: '5G uyumlu telefon öner', 'iPhone 16 Pro sipariş oluştur')")

if user_text:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # Call API
    with st.chat_message("assistant"):
        with st.spinner("Yanıt hazırlanıyor..."):
            try:
                # Backend'in payload şemasına uyumlu olacak şekilde basit ve esnek gönderiyoruz:
                # 1) {"message": "..."} (en yaygın)
                # 2) thread_id destekliyse ekliyoruz
                payload = {"message": user_text}
                if thread_id.strip():
                    payload["thread_id"] = thread_id.strip()

                r = requests.post(api_url, json=payload, timeout=int(timeout_s))

                if r.status_code >= 400:
                    st.error(f"HTTP {r.status_code}")
                    st.code(r.text)
                    assistant_text = f"Sunucu hata döndürdü: HTTP {r.status_code}"
                else:
                    try:
                        data = r.json()
                    except Exception:
                        data = {"raw_text": r.text}

                    assistant_text = extract_answer(data)
                    st.markdown(assistant_text)

                    if show_raw:
                        st.divider()
                        st.subheader("Ham JSON")
                        st.code(json.dumps(data, ensure_ascii=False, indent=2))

            except requests.exceptions.ConnectionError:
                assistant_text = (
                    "API'ye bağlanamadım. FastAPI çalışıyor mu?\n\n"
                    f"- Beklenen: {base_url}\n"
                    "- Komut: `uvicorn --app-dir src vfa.app.main:app --reload --port 8000`"
                )
                st.error(assistant_text)
            except requests.exceptions.Timeout:
                assistant_text = "İstek zaman aşımına uğradı. Timeout değerini artırmayı deneyebilirsin."
                st.error(assistant_text)
            except Exception as e:
                assistant_text = f"Bilinmeyen hata: {repr(e)}"
                st.error(assistant_text)

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
