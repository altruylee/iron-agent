"""Stage a local folder or Git URL under tools/packages."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def slug(value: str) -> str:
    import re

    value = value.rstrip("/").split("/")[-1].replace(".git", "")
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value.lower()).strip("-") or "package"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source", required=True)
    parser.add_argument("--name", default="")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    source = args.source
    name = args.name or slug(source)
    target = root / "tools" / "packages" / name

    if target.exists():
        if not args.overwrite:
            raise SystemExit(f"Target exists: {target}. Use --overwrite.")
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    if source.startswith("http://") or source.startswith("https://") or source.endswith(".git"):
        subprocess.run(["git", "clone", source, str(target)], check=True)
    else:
        src_path = Path(source).expanduser().resolve()
        if not src_path.is_dir():
            raise SystemExit(f"Source must be a directory or Git URL: {source}")
        shutil.copytree(src_path, target)

    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

