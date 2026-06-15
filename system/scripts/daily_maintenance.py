"""Run daily idle maintenance for Iron Agent."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


TZ = timezone(timedelta(hours=8))


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":", 1)
    return int(hour), int(minute)


def in_idle_window(now: datetime, start: str, end: str) -> bool:
    start_h, start_m = parse_hhmm(start)
    end_h, end_m = parse_hhmm(end)
    current = now.hour * 60 + now.minute
    start_min = start_h * 60 + start_m
    end_min = end_h * 60 + end_m
    if start_min <= end_min:
        return start_min <= current <= end_min
    return current >= start_min or current <= end_min


def should_run(now: datetime, state: dict, min_hours: int) -> bool:
    last_run = state.get("last_run_at")
    if not last_run:
        return True
    try:
        previous = datetime.fromisoformat(last_run)
    except ValueError:
        return True
    return now - previous >= timedelta(hours=min_hours)


def run_python(script: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def write_report(root: Path, now: datetime, lines: list[str]) -> Path:
    report_dir = root / "output" / "maintenance"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{now.date().isoformat()}-daily-maintenance.md"
    body = [
        "# Daily Maintenance Report",
        "",
        "## Directory",
        "",
        "- [Summary](#summary)",
        "- [Details](#details)",
        "",
        "## Summary",
        "",
        f"- Run time: `{now.isoformat(timespec='seconds')}`",
        "",
        "## Details",
        "",
        *[f"- {line}" for line in lines],
        "",
    ]
    report_path.write_text("\n".join(body), encoding="utf-8")
    return report_path


def append_task_log(root: Path, report_path: Path, verification: str) -> None:
    script = root / "system" / "scripts" / "append_task_log.py"
    run_python(
        script,
        [
            "--root",
            str(root),
            "--task",
            "Daily idle maintenance",
            "--type",
            "maintenance",
            "--permission",
            "P1",
            "--read",
            "config/maintenance.json;workspace/memory/INDEX.md;workspace/meta/task-log.jsonl",
            "--written",
            f"workspace/meta/memory-candidates.md;workspace/meta/maintenance-state.json;workspace/memory/semantic/sops/;{report_path.relative_to(root)};workspace/meta/task-log.jsonl",
            "--commands",
            "python system/scripts/daily_maintenance.py;python system/scripts/compact_memory.py;python system/scripts/shadow_reviewer.py",
            "--verification",
            verification,
            "--memory-candidates",
            "Iron Agent can run daily idle maintenance through daily_maintenance.py using config/maintenance.json",
        ],
    )


def write_codex_trigger(root: Path, now: datetime, status: str) -> Path:
    trigger_path = root / "workspace" / "meta" / "codex-automation-trigger.json"
    trigger_path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "created_at": now.isoformat(timespec="seconds"),
        "status": status,
        "next_step": "Codex automation should run AI shadow review against workspace/memory/shadow-review/.",
        "prompt": "system/prompts/codex-shadow-maintenance.md",
    }
    trigger_path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    return trigger_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = root / "config" / "maintenance.json"
    state_path = root / "workspace" / "meta" / "maintenance-state.json"

    config = load_json(config_path, {})
    daily = config.get("daily_maintenance", {})
    now = datetime.now(TZ)
    lines: list[str] = []

    if not daily.get("enabled", True):
        print("Daily maintenance disabled")
        return 0

    idle = daily.get("idle_window", {})
    start = idle.get("start", "23:00")
    end = idle.get("end", "06:00")
    min_hours = int(daily.get("min_hours_between_runs", 20))
    state = load_json(state_path, {})

    if not args.force and not in_idle_window(now, start, end):
        print(f"Outside idle window {start}-{end}; use --force to run now")
        return 0

    if not args.force and not should_run(now, state, min_hours):
        print(f"Last run is too recent; min_hours_between_runs={min_hours}")
        return 0

    compact_script = root / "system" / "scripts" / "compact_memory.py"
    compact_args = [
        "--root",
        str(root),
        "--limit",
        str(int(daily.get("max_memory_candidates", 50))),
    ]
    if daily.get("auto_apply_memory", False):
        compact_args.append("--apply")

    result = run_python(compact_script, compact_args)
    lines.append(result.stdout.strip() or "Memory candidate preparation completed")
    if result.stderr.strip():
        lines.append(f"stderr: {result.stderr.strip()}")

    shadow_script = root / "system" / "scripts" / "shadow_reviewer.py"
    shadow_result = run_python(shadow_script, ["--root", str(root)])
    lines.append(shadow_result.stdout.strip() or "Shadow review completed")
    if shadow_result.stderr.strip():
        lines.append(f"shadow stderr: {shadow_result.stderr.strip()}")

    slim_script = root / "system" / "scripts" / "memory_index_maintenance.py"
    slim_result = run_python(slim_script, ["--root", str(root), "--apply", "--write-report"])
    lines.append(slim_result.stdout.strip() or "Memory index slimming completed")
    if slim_result.stderr.strip():
        lines.append(f"index stderr: {slim_result.stderr.strip()}")

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "last_run_at": now.isoformat(timespec="seconds"),
        "last_status": "ok" if result.returncode == 0 and shadow_result.returncode == 0 and slim_result.returncode == 0 else "error",
        "auto_apply_memory": bool(daily.get("auto_apply_memory", False)),
        "shadow_review": bool(daily.get("shadow_review", True)),
    }
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    lines.append(f"State updated: {state_path.relative_to(root)}")

    trigger_path = write_codex_trigger(root, now, state["last_status"])
    lines.append(f"Codex trigger written: {trigger_path.relative_to(root)}")

    report_path = root / "output" / "maintenance" / f"{now.date().isoformat()}-daily-maintenance.md"
    if daily.get("write_report", True):
        report_path = write_report(root, now, lines)
        lines.append(f"Report written: {report_path.relative_to(root)}")

    append_task_log(root, report_path, "daily maintenance completed")

    print("\n".join(lines))
    return result.returncode or shadow_result.returncode or slim_result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
