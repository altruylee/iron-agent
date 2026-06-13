"""Install Iron Agent Pack into a target directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
}

EXCLUDE_PREFIXES = {
    "output",
    "backups",
    "workspace/meta/task-log.jsonl",
    "workspace/meta/maintenance-state.json",
    "workspace/meta/memory-candidates.md",
    "workspace/meta/scheduled-task-state.json",
    "workspace/meta/codex-automation-state.md",
    "workspace/meta/codex-automation-trigger.json",
}

RUNTIME_DIRS = [
    "inbox",
    "output",
    "output/research",
    "output/maintenance",
    "output/evolution",
    "output/skill-audits",
    "watchlists",
    "hypotheses",
    "tools",
    "tools/packages",
    "backups",
    "wiki/raw",
    "wiki/sources",
    "wiki/entities",
    "wiki/concepts",
    "wiki/explorations",
    "workspace/meta",
]

RUNTIME_FILES = [
    "workspace/meta/task-log.jsonl",
]


def should_skip(src_root: Path, path: Path) -> bool:
    rel = path.relative_to(src_root).as_posix()
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    return any(rel.startswith(prefix) for prefix in EXCLUDE_PREFIXES)


def copy_pack(src: Path, target: Path, overwrite: bool) -> None:
    if target.exists() and any(target.iterdir()) and not overwrite:
        raise SystemExit(f"Target is not empty: {target}. Use --overwrite to replace files.")
    if target.exists() and overwrite:
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    for path in src.rglob("*"):
        if should_skip(src, path):
            continue
        rel = path.relative_to(src)
        dest = target / rel
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)

    for rel in RUNTIME_DIRS:
        (target / rel).mkdir(parents=True, exist_ok=True)
    for rel in RUNTIME_FILES:
        file_path = target / rel
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch(exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--source", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--skip-scheduler", action="store_true", help="Accepted for installer UX; no scheduler is created by install.py.")
    parser.add_argument("--skip-codex-automation", action="store_true", help="Accepted for installer UX; no Codex automation is created by install.py.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned install paths without copying.")
    parser.add_argument("--portable", action="store_true", help="Install as a portable workspace with no external side effects.")
    args = parser.parse_args()

    src = Path(args.source).resolve()
    target = Path(args.target).expanduser().resolve()
    if args.dry_run:
        print(f"Source: {src}")
        print(f"Target: {target}")
        print("External schedulers: not created by install.py")
        return 0
    copy_pack(src, target, args.overwrite)
    print(f"Iron Agent Pack installed to: {target}")
    print(f"Next: open {target / 'AGENTS.md'} with Codex and run initial install.")
    if args.portable or args.skip_scheduler or args.skip_codex_automation:
        print("Portable mode: external schedulers and Codex automations were not created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
