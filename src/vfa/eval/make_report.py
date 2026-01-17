import json
from pathlib import Path
from statistics import mean

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load_summary(run_dir: Path):
    p = run_dir / "summary.json"
    return read_json(p) if p.exists() else None

def main():
    results_dir = Path("src/vfa/eval/results")
    runs = sorted([p for p in results_dir.iterdir() if p.is_dir() and (p/"summary.json").exists()])

    lines = []
    lines.append("# VF Chatbot Evaluation Report\n")
    lines.append("## Runs\n")

    for r in runs:
        s = load_summary(r)
        lines.append(f"### {r.name}\n")
        lines.append("```json\n" + json.dumps(s, ensure_ascii=False, indent=2) + "\n```\n")

    out = results_dir / "REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote:", out)

if __name__ == "__main__":
    main()
