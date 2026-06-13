"""Install an audited Markdown skill into system/skills."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def slug(value: str) -> str:
    import re

    value = re.sub(r"[^a-zA-Z0-9-]+", "-", value.strip().lower())
    return value.strip("-") or "installed-skill"


def source_skill_file(source: Path) -> Path:
    if source.is_file() and source.suffix.lower() == ".md":
        return source
    if source.is_dir() and (source / "SKILL.md").exists():
        return source / "SKILL.md"
    raise FileNotFoundError("Source must be a .md file or a folder containing SKILL.md")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source", required=True)
    parser.add_argument("--name", default="")
    parser.add_argument("--allow-risk", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    source = Path(args.source).expanduser().resolve()
    audit_script = root / "system" / "scripts" / "audit_skill.py"

    audit = subprocess.run(
        [sys.executable, str(audit_script), "--root", str(root), "--source", str(source)],
        text=True,
        capture_output=True,
        check=False,
    )
    print(audit.stdout, end="")
    if audit.stderr:
        print(audit.stderr, file=sys.stderr, end="")
    if audit.returncode != 0 and not args.allow_risk:
        print("Install blocked: audit found medium/high risk. Re-run with --allow-risk only after explicit user approval.")
        return audit.returncode

    skill_file = source_skill_file(source)
    name = args.name or slug(skill_file.stem if skill_file.name != "SKILL.md" else source.name)
    target = root / "system" / "skills" / f"{name}.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        raise FileExistsError(f"Target already exists: {target}")

    shutil.copy2(skill_file, target)
    print(f"Installed skill: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
