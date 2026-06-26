"""Clean runtime and local-only state before publishing Iron Agent."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


RUNTIME_DIRS = [
    "output",
    "backups",
    "inbox",
    "wiki/raw",
    "wiki/sources",
    "wiki/entities",
    "wiki/concepts",
    "wiki/explorations",
]

STATE_FILES = [
    "workspace/meta/task-log.jsonl",
    "workspace/meta/maintenance-state.json",
    "workspace/meta/memory-candidates.md",
    "workspace/meta/scheduled-task-state.json",
    "workspace/meta/codex-automation-state.md",
    "workspace/meta/codex-automation-trigger.json",
    "workspace/meta/package-registry.json",
    "workspace/meta/semantic-cache.json",
    "workspace/meta/token-cache.json",
    "workspace/memory/semantic_index.jsonl",
    "workspace/memory/semantic_vectors.jsonl",
]


def ensure_root(root: Path) -> None:
    if not (root / "AGENTS.md").exists() or not (root / "manifest.json").exists():
        raise SystemExit(f"Not an Iron Agent root: {root}")


def clean_dir(path: Path, apply: bool, actions: list[str]) -> None:
    if not path.exists():
        return
    for child in path.iterdir():
        if child.name == ".gitkeep":
            continue
        actions.append(f"remove {child}")
        if apply:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()


def clean_file(path: Path, apply: bool, actions: list[str]) -> None:
    if not path.exists():
        return
    if path.name == "task-log.jsonl":
        actions.append(f"truncate {path}")
        if apply:
            path.write_text("", encoding="utf-8")
        return
    actions.append(f"remove {path}")
    if apply:
        path.unlink()


def remove_test_copy(root: Path, apply: bool, actions: list[str]) -> None:
    test_copy = root.parent / "iron-agent-install-test"
    if not test_copy.exists():
        return
    actions.append(f"remove test copy {test_copy}")
    if apply:
        shutil.rmtree(test_copy)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--include-test-copy", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ensure_root(root)
    actions: list[str] = []

    for rel in RUNTIME_DIRS:
        clean_dir(root / rel, args.apply, actions)
        if args.apply:
            (root / rel).mkdir(parents=True, exist_ok=True)

    for rel in STATE_FILES:
        clean_file(root / rel, args.apply, actions)

    if args.include_test_copy:
        remove_test_copy(root, args.apply, actions)

    if not actions:
        print("Nothing to clean")
        return 0

    for action in actions:
        print(action)
    if not args.apply:
        print("Dry run only. Re-run with --apply to clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
