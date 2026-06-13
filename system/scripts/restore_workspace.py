"""Restore an Iron Agent backup archive."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--archive", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    archive_path = Path(args.archive).expanduser().resolve()
    if not args.dry_run and not args.apply:
        raise SystemExit("Use --dry-run or --apply")

    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        for name in names:
            print(name)
        if args.apply:
            archive.extractall(root)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

