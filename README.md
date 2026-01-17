# Agentic Telco Assistant — 5G Domain-Expert Agentic Assistant (RAG + Tools + Order Creation)

A telecom-focused agentic assistant that behaves like a **5G domain expert**:  
- Answers 5G technical questions (grounded via RAG)  
- Recommends 5G-compatible devices (catalog discovery + selection)  
- Creates installment-based orders by interacting with backend systems  
- Provides an evaluation pipeline with metrics + optional LLM-as-a-judge scoring

Repo: https://github.com/didarslan/VF_Chatbot

---

## Key Features

- **Agentic workflow orchestration:** `ManagerAgent` routes requests to specialized modules
- **Stateful multi-turn flows:** slot extraction & state updates (installment, city, MSISDN, selected device/url)
- **RAG grounding for 5G knowledge:** reduces hallucinations and improves factuality
- **Tool use:** device catalog discovery/selection, backend order creation
- **Evaluation suite:** dataset-driven runner that logs per-sample outputs and aggregates metrics
- **UI + API:** Streamlit UI and FastAPI endpoint for interactive usage

---

## Architecture (High Level)

**Entry point:** `ManagerAgent.handle(thread_id, message)`  
- Updates conversation state (slots can be provided any time)
- Runs intent analysis (LLM/heuristics + state-aware overrides)
- Routes to:
  - **Knowledge Agent (RAG)** for 5G Q&A
  - **Device Agent / Catalog Tool** for discovery & selection
  - **Order Agent** for order creation (requires missing-slot completion)
  - **Response Composer** for consistent user-facing answers

Code map:
- Manager agent: `src/vfa/agents/manager.py`
- Services: `src/vfa/services/`
- Tools: `src/vfa/tools/`
- API: `src/vfa/app/api.py`
- Eval: `src/vfa/eval/`

---

## Repository Structure

```text
VF_Chatbot/
├─ src/
│  └─ vfa/
│     ├─ agents/          # routing/orchestration (ManagerAgent)
│     ├─ services/        # intent, rag, composer, llm utils, scraping/parsing
│     ├─ tools/           # phone catalog tool integrations
│     ├─ app/             # FastAPI endpoints
│     ├─ core/            # config, schemas, prompts
│     └─ eval/            # datasets, runner, results
├─ scripts/               # helper scripts (dataset seeding, utilities)
├─ tests/                 # tests (optional)
├─ ui_streamlit.py        # Streamlit UI entrypoint
└─ pyproject.toml         # dependencies


## Setup
1) Create and activate a virtual environment.
2) Install dependencies:
```bash
pip install -e .
```
3) Create `.env` in the repo root:
```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

## Run the API
```bash
uvicorn --app-dir src vfa.app.main:app --reload --port 8000
```
Health check:
```
http://127.0.0.1:8000/health
```

## Run the Streamlit UI
```bash
streamlit run ui_streamlit.py
```
The UI connects to the API base URL (default `http://127.0.0.1:8000`).

## Run evals
Single run:
```bash
python -m vfa.eval.run_eval --dataset src/vfa/eval/datasets/manual_eval.jsonl --out src/vfa/eval/results/manual_run
```
With limits/timeouts:
```bash
python -m vfa.eval.run_eval --dataset src/vfa/eval/datasets/manual_eval.jsonl --out src/vfa/eval/results/manual_run --limit 10 --timeout_s 60
```
Disable judge:
```bash
python -m vfa.eval.run_eval --dataset src/vfa/eval/datasets/manual_eval.jsonl --out src/vfa/eval/results/manual_run --no_judge
```

## Notes
- The eval runner loads `.env` automatically.
- Chroma data persists in `data/` (configurable via `CHROMA_DIR`).
- For judge settings, use `JUDGE_MODEL`, `JUDGE_TIMEOUT_S`, and `JUDGE_MAX_RETRIES`.
