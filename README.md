# Vodafone Agentic Assistant

Vodafone TR agentic assistant for 5G Q&A, device discovery, and order workflows. The system combines a FastAPI backend, LangChain-based LLM calls, and optional RAG over a local vector store.

## Features
- Intent routing for greetings, device discovery/selection, 5G knowledge, and order flow.
- RAG-backed knowledge answers using Chroma.
- Safety guard for sensitive data requests.
- Evaluation runner with LLM judge support.
- Streamlit UI for quick manual testing.

## Repository layout
- `src/vfa/`: main package
  - `app/`: FastAPI app and routes
  - `agents/`: orchestration and domain agents
  - `services/`: LLM, RAG, safety, state, and utility services
  - `eval/`: evaluation runner, judge client, datasets, and metrics
- `ui_streamlit.py`: Streamlit UI for manual testing
- `data/`: local data and vector indexes

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
