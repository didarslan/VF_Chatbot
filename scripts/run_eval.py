from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vfa.agents.manager import ManagerAgent
from vfa.eval.rubics import simple_auto_metrics


DATASET = ROOT / "src" / "vfa" / "eval" / "datasets" / "manual_eval.jsonl"


def main() -> None:
    agent = ManagerAgent()
    rows = []

    with open(DATASET, "r", encoding="utf-8") as f:
        for line in f:
            ex = json.loads(line)
            thread_id = ex.get("thread_id", "eval")
            message = ex["message"]

            result = agent.handle(thread_id=thread_id, message=message)
            m = simple_auto_metrics(message=message, manager_result=result)

            rows.append({
                "message": message,
                "intent": result.intent,
                "answer": result.message,
                "has_sources": m["has_sources"],
                "dont_know_ok": m["dont_know_ok"],
                "tool_calls": len(result.tool_logs),
            })

    out_path = ROOT / "eval_results.json"
    with open(out_path, "w", encoding="utf-8") as wf:
        json.dump(rows, wf, ensure_ascii=False, indent=2)

    print("[OK] wrote:", out_path)
    print("Examples:", len(rows))


if __name__ == "__main__":
    main()
