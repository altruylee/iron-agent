"""Check and report low-token memory index health."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path


TZ = timezone(timedelta(hours=8))

LIMITS = {
    "workspace/memory/INDEX.md": 50,
    "workspace/memory/hot/INDEX.md": 50,
    "workspace/memory/warm/INDEX.md": 100,
    "workspace/memory/cold/INDEX.md": 150,
}


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def classify_index(path: Path, root: Path) -> int:
    rel = path.relative_to(root).as_posix()
    if rel in LIMITS:
        return LIMITS[rel]
    if rel.endswith("/INDEX.md"):
        depth = len(Path(rel).parts)
        if depth <= 4:
            return 100
        return 150
    if "/semantic/sops/" in rel:
        return 200
    return 300


def ensure_hot_warm_cold(root: Path) -> list[str]:
    actions: list[str] = []
    for rel in ["workspace/memory/hot/INDEX.md", "workspace/memory/warm/INDEX.md", "workspace/memory/cold/INDEX.md"]:
        path = root / rel
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        title = path.parent.name.title()
        path.write_text(f"# {title} Memory Index\n\n## Directory\n\n- [Routes](#routes)\n\n## Routes\n\n| Topic | Path |\n|---|---|\n", encoding="utf-8")
        actions.append(f"created {rel}")
    return actions


def check_limits(root: Path) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for path in (root / "workspace" / "memory").rglob("*.md"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if not rel.endswith("INDEX.md") and "/semantic/sops/" not in rel:
            continue
        count = line_count(path)
        limit = classify_index(path, root)
        if count > limit:
            violations.append({"path": rel, "lines": count, "limit": limit})
    return violations


def write_report(root: Path, actions: list[str], violations: list[dict[str, object]]) -> Path:
    report_dir = root / "workspace" / "meta"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "memory-index-health.md"
    lines = [
        "# Memory Index Health",
        "",
        "## Directory",
        "",
        "- [Summary](#summary)",
        "- [Actions](#actions)",
        "- [Violations](#violations)",
        "",
        "## Summary",
        "",
        f"- Actions: `{len(actions)}`",
        f"- Violations: `{len(violations)}`",
        "",
        "## Actions",
        "",
        *[f"- {item}" for item in actions],
        "",
        "## Violations",
        "",
    ]
    if violations:
        lines.extend(f"- `{item['path']}` has `{item['lines']}` lines; limit `{item['limit']}`" for item in violations)
    else:
        lines.append("- None")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def rebuild_index_json(root: Path) -> Path:
    index_path = root / "workspace" / "memory" / "index.json"
    if index_path.exists():
        return index_path
    index_path.write_text(json.dumps({}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    actions: list[str] = []
    if args.apply:
        actions.extend(ensure_hot_warm_cold(root))
        rebuild_index_json(root)
    violations = check_limits(root)
    report = write_report(root, actions, violations) if args.write_report else None
    payload = {"ok": not violations, "actions": actions, "violations": violations, "report": str(report) if report else None}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(report)
        for item in violations:
            print(f"{item['path']}: {item['lines']} > {item['limit']}")
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
