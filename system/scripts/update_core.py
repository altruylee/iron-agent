"""Update core Iron Agent files from another pack copy."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PRESERVE_PREFIXES = [
    "workspace/meta",
    "wiki",
    "packs/domain-agents",
    "watchlists",
    "hypotheses",
    "inbox",
    "output",
    "backups",
    "tools/packages",
]


def preserved(rel: str) -> bool:
    return any(rel == prefix or rel.startswith(prefix + "/") for prefix in PRESERVE_PREFIXES)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        raise SystemExit("Use --dry-run or --apply")

    root = Path(args.root).resolve()
    source = Path(args.source).expanduser().resolve()
    changes: list[str] = []

    for path in source.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(source).as_posix()
        if preserved(rel) or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        target = root / rel
        changes.append(rel)
        if args.apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

    for rel in changes:
        print(rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

