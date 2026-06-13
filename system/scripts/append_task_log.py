"""Append one structured task log entry to workspace/meta/task-log.jsonl."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


TZ = timezone(timedelta(hours=8))


def parse_list(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--task", required=True)
    parser.add_argument("--type", required=True)
    parser.add_argument("--permission", required=True)
    parser.add_argument("--read", default="")
    parser.add_argument("--written", default="")
    parser.add_argument("--commands", default="")
    parser.add_argument("--verification", default="")
    parser.add_argument("--memory-candidates", default="")
    parser.add_argument("--friction", default="")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    log_path = root / "workspace" / "meta" / "task-log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "time": datetime.now(TZ).isoformat(timespec="seconds"),
        "task": args.task,
        "type": args.type,
        "permission": args.permission,
        "read": parse_list(args.read),
        "written": parse_list(args.written),
        "commands": parse_list(args.commands),
        "verification": args.verification,
        "memory_candidates": parse_list(args.memory_candidates),
        "friction": parse_list(args.friction),
    }

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

