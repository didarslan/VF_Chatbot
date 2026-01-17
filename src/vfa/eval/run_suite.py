import os
import subprocess

DATASET = r"src\vfa\eval\datasets\manual_eval.jsonl"
OUT_BASE = r"src\vfa\eval\results"

SUITE = [
    ("baseline", {"RAG_ENABLED": "1", "RAG_TOPK": "5"}),
    ("rag_off",  {"RAG_ENABLED": "0"}),
    ("topk_3",   {"RAG_ENABLED": "1", "RAG_TOPK": "3"}),
]

for name, env_add in SUITE:
    env = os.environ.copy()
    env.update(env_add)
    out_dir = rf"{OUT_BASE}\suite_{name}"
    cmd = ["python", r"src\vfa\eval\run_eval.py", "--dataset", DATASET, "--out", out_dir]
    print("Running:", name, "->", out_dir)
    subprocess.check_call(cmd, env=env)
