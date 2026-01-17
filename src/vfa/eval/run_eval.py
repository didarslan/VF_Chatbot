# src/vfa/eval/run_eval.py
import argparse
import concurrent.futures
import json
import os
import time
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

from . import metrics, rubics

from vfa.agents.manager import ManagerAgent


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_handle_output(res: Any) -> Dict[str, Any]:
    """ChatResponse (pydantic) -> dict"""
    if hasattr(res, "model_dump"):
        d = res.model_dump()
        d["answer"] = d.get("answer") or ""
        d.setdefault("actions", [])
        d.setdefault("state", {})
        d.setdefault("debug", {})
        return d
    if hasattr(res, "dict"):
        d = res.dict()
        d["answer"] = d.get("answer") or ""
        d.setdefault("actions", [])
        d.setdefault("state", {})
        d.setdefault("debug", {})
        return d
    if isinstance(res, dict):
        res["answer"] = res.get("answer") or ""
        res.setdefault("actions", [])
        res.setdefault("state", {})
        res.setdefault("debug", {})
        return res
    return {"answer": str(res), "raw": repr(res), "actions": [], "state": {}, "debug": {}}


def percentile(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    xs = sorted(values)
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="jsonl dataset path")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--limit", type=int, default=0, help="optional limit")
    ap.add_argument("--timeout_s", type=int, default=15, help="per-sample timeout seconds")
    ap.add_argument("--no_judge", action="store_true", help="disable LLM-judge rubric scoring")
    ap.add_argument("--print_every", type=int, default=1, help="progress print frequency")
    ap.add_argument("--sleep_s", type=float, default=0.0, help="sleep between samples")
    args = ap.parse_args()

    dataset_path = Path(args.dataset)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("== Eval runner ==")
    print("CWD:", Path.cwd())
    print("Dataset:", dataset_path.resolve())
    print("Out:", out_dir.resolve())
    print("timeout_s:", args.timeout_s, "no_judge:", args.no_judge)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path.resolve()}")

    data = load_jsonl(dataset_path)
    if args.limit and args.limit > 0:
        data = data[: args.limit]

    print("Loaded N:", len(data))

    agent = ManagerAgent()
    results: List[Dict[str, Any]] = []

    for i, ex in enumerate(data):
        q = ex.get("input") or ex.get("question") or ex.get("prompt")
        if not q:
            results.append({"id": ex.get("id"), "error": "missing_input_field", "example": ex})
            continue

        # ✅ each sample isolated state unless user explicitly groups with thread_id
        tid = ex.get("thread_id") or ex.get("id") or f"eval_{i}"

        if args.print_every and (i % args.print_every == 0):
            print(f"[{i+1}/{len(data)}] id={ex.get('id')} exp_route={ex.get('expected_route')}", flush=True)

        pred = {"answer": "", "actions": [], "state": {}, "debug": {}}
        err = None

        t0 = time.perf_counter()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(agent.handle, str(tid), q)
                res = fut.result(timeout=args.timeout_s)
            pred = normalize_handle_output(res)
        except concurrent.futures.TimeoutError:
            err = f"TimeoutError: handle() exceeded {args.timeout_s}s"
        except Exception as e:
            err = f"{type(e).__name__}: {e}"

        latency_ms = (time.perf_counter() - t0) * 1000

        # auto metrics
        try:
            auto = metrics.compute_metrics(ex, pred)
        except Exception as e:
            auto = {"metric_error": f"{type(e).__name__}: {e}"}

        # judge rubric (optional)
        if args.no_judge:
            judge = {"skipped": True, "reason": "disabled_by_flag"}
        else:
            try:
                judge = rubics.judge(ex, pred)
            except Exception as e:
                judge = {"judge_error": f"{type(e).__name__}: {e}"}

        row = {
            "id": ex.get("id"),
            "thread_id": tid,
            "tags": ex.get("tags", []),
            "question": q,
            "expected": ex.get("expected"),
            "prediction": pred,
            "auto_metrics": auto,
            "judge": judge,
            "latency_ms": latency_ms,
        }
        if err:
            row["error"] = err

        results.append(row)
        
        if args.sleep_s and args.sleep_s > 0:
            time.sleep(args.sleep_s)

    # ✅ write per-sample
    per_sample_path = out_dir / "per_sample.jsonl"
    with per_sample_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ✅ summary aggregations
    lat = [r["latency_ms"] for r in results if isinstance(r.get("latency_ms"), (int, float))]
    route_accs = []
    action_accs = []
    refusal_ok = []

    for r in results:
        am = r.get("auto_metrics") or {}
        if isinstance(am, dict):
            if isinstance(am.get("route_acc"), (int, float)):
                route_accs.append(am["route_acc"])
            if isinstance(am.get("action_acc"), (int, float)):
                action_accs.append(am["action_acc"])
            if isinstance(am.get("refusal_ok"), (int, float)):
                refusal_ok.append(am["refusal_ok"])

    judge_overall = []
    for r in results:
        j = r.get("judge") or {}
        if isinstance(j, dict) and isinstance(j.get("overall"), int):
            judge_overall.append(j["overall"])

    summary = {
        "n": len(results),
        "errors": sum(1 for r in results if r.get("error")),
        "avg_latency_ms": mean(lat) if lat else None,
        "p95_latency_ms": percentile(lat, 0.95),
        "route_acc_avg": mean(route_accs) if route_accs else None,
        "action_acc_avg": mean(action_accs) if action_accs else None,
        "refusal_ok_avg": mean(refusal_ok) if refusal_ok else None,
        "judge_overall_avg": mean(judge_overall) if judge_overall else None,
        "judge_enabled": (not args.no_judge),
        "env": {
            "EVAL_MODE": os.getenv("EVAL_MODE"),
            "RAG_ENABLED": os.getenv("RAG_ENABLED"),
            "RAG_TOPK": os.getenv("RAG_TOPK"),
            "JUDGE_MODEL": os.getenv("JUDGE_MODEL"),
        },
        "out_dir": str(out_dir.resolve()),
    }

    summary_path = out_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("Wrote:", per_sample_path.resolve())
    print("Wrote:", summary_path.resolve())
    print("Summary:", json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

