"""Run release-oriented checks for publishing Iron Agent."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


SKIP_FILES = {"system/scripts/release_check.py"}

FORBIDDEN_PATTERNS = [
    re.compile(r"\b[A-Za-z]:\\Users\\", re.IGNORECASE),
    re.compile(r"\bD:\\DOC\\", re.IGNORECASE),
    re.compile(r"\baltru\b", re.IGNORECASE),
    re.compile(r"iron-agent-shadow-review", re.IGNORECASE),
]

SKIP_DIRS = {".git", "__pycache__", "output", "backups", "tools", "iron.egg-info"}


def skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    if rel in SKIP_FILES:
        return True
    return any(part in SKIP_DIRS for part in path.relative_to(root).parts)


def required_files(root: Path) -> list[str]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    required = manifest.get("required", [])
    if not isinstance(required, list):
        raise SystemExit("manifest.json required must be a list")
    return [str(item) for item in required]


def run(cmd: list[str]) -> int:
    print(" ".join(cmd))
    return subprocess.run(cmd, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    failures: list[str] = []
    for rel in required_files(root):
        if not (root / rel).exists():
            failures.append(f"missing {rel}")

    for path in root.rglob("*"):
        if not path.is_file() or skip(path, root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                failures.append(f"local-only value in {path.relative_to(root).as_posix()}: {pattern.pattern}")

    if run([sys.executable, str(root / "system/scripts/structure_integrity.py"), "--root", str(root)]) != 0:
        failures.append("structure_integrity failed")
    if run([sys.executable, str(root / "system/scripts/health_check.py"), "--root", str(root)]) != 0:
        failures.append("health_check failed")

    if failures:
        print("Release check failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Release check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
