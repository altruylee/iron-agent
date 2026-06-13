"""Generate a simple evolution report from task logs and friction logs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    log_path = root / "workspace" / "meta" / "task-log.jsonl"
    task_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()
    memory_candidates = 0

    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            task_counter[entry.get("task", "unknown")] += 1
            type_counter[entry.get("type", "unknown")] += 1
            memory_candidates += len(entry.get("memory_candidates", []))

    report_dir = root / "output" / "evolution"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / f"{datetime.now().strftime('%Y-%m-%d')}-evolution-report.md"
    lines = [
        "# Evolution Report",
        "",
        "## Directory",
        "",
        "- [Summary](#summary)",
        "- [Repeated Tasks](#repeated-tasks)",
        "- [Task Types](#task-types)",
        "- [Recommendations](#recommendations)",
        "",
        "## Summary",
        "",
        f"- Memory candidates observed: `{memory_candidates}`",
        "",
        "## Repeated Tasks",
        "",
    ]
    lines.extend(f"- `{task}`: {count}" for task, count in task_counter.most_common(20))
    lines += ["", "## Task Types", ""]
    lines.extend(f"- `{task_type}`: {count}" for task_type, count in type_counter.most_common())
    lines += [
        "",
        "## Recommendations",
        "",
        "- Promote repeated tasks into skills when the same task appears 3+ times.",
        "- Review memory candidates after maintenance runs.",
        "- Put domain-specific workflows in `packs/domain-agents/`.",
        "",
    ]
    report.write_text("\n".join(lines), encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

