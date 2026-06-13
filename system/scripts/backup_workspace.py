"""Create a zip backup of durable Iron Agent user state."""

from __future__ import annotations

import argparse
import zipfile
from datetime import datetime
from pathlib import Path


INCLUDE = [
    "AGENTS.md",
    "CLAUDE.md",
    "workspace",
    "wiki",
    "packs/domain-agents",
    "watchlists",
    "hypotheses",
    "config",
]


def iter_files(root: Path):
    for rel in INCLUDE:
        path = root / rel
        if path.is_file():
            yield path
        elif path.is_dir():
            yield from (item for item in path.rglob("*") if item.is_file())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    output = Path(args.output).resolve() if args.output else backup_dir / f"iron-agent-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in iter_files(root):
            archive.write(path, path.relative_to(root).as_posix())

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

