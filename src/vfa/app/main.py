from fastapi import FastAPI
from vfa.app.api import router

app = FastAPI(title="Vodafone Agentic Assistant")
app.include_router(router)

@app.get("/health")
def health():
    return {"ok": True}
