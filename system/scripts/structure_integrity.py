"""Verify Iron Agent Markdown directories and local links."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SKIP_DIRS = {
    ".git",
    "__pycache__",
    "backups",
    "node_modules",
    "tools/packages",
}

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def is_skipped(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(rel == item or rel.startswith(f"{item}/") for item in SKIP_DIRS)


def is_external_or_placeholder(target: str) -> bool:
    lowered = target.lower()
    return (
        not target
        or target.startswith("#")
        or "{" in target
        or "}" in target
        or lowered.startswith(("http://", "https://", "mailto:", "app://"))
    )


def strip_anchor(target: str) -> str:
    return target.split("#", 1)[0].strip()


def resolve_link(md_file: Path, root: Path, target: str) -> Path:
    clean = strip_anchor(target).replace("%20", " ")
    if re.match(r"^[A-Za-z]:[\\/]", clean):
        return Path(clean)
    candidate = (md_file.parent / clean).resolve()
    if candidate.exists():
        return candidate
    return (root / clean).resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    markdown_files = [
        path
        for path in root.rglob("*.md")
        if path.is_file() and not is_skipped(path, root)
    ]

    missing_directory: list[str] = []
    broken_links: list[str] = []

    for md_file in markdown_files:
        rel = md_file.relative_to(root).as_posix()
        text = md_file.read_text(encoding="utf-8", errors="replace")
        if "\n## Directory" not in f"\n{text}":
            missing_directory.append(rel)

        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            if is_external_or_placeholder(target):
                continue
            clean = strip_anchor(target)
            if not clean:
                continue
            resolved = resolve_link(md_file, root, clean)
            if not resolved.exists():
                broken_links.append(f"{rel} -> {target}")

    if missing_directory or broken_links:
        if missing_directory:
            print("Missing ## Directory:")
            for item in missing_directory:
                print(f"- {item}")
        if broken_links:
            print("Broken local links:")
            for item in broken_links:
                print(f"- {item}")
        return 1

    print("Structure integrity OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
