"""Run the minimal Iron Agent pack smoke test."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--with-output-generators",
        action="store_true",
        help="Also run scripts that write reports/backups under output/ and backups/.",
    )
    parser.add_argument("--release", action="store_true", help="Run release checks as well.")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    run([sys.executable, str(root / "system/scripts/health_check.py"), "--root", str(root)])
    run([sys.executable, str(root / "system/scripts/structure_integrity.py"), "--root", str(root)])
    if args.with_output_generators:
        run([sys.executable, str(root / "system/scripts/evolution_report.py"), "--root", str(root)])
        run([sys.executable, str(root / "system/scripts/backup_workspace.py"), "--root", str(root)])
    if args.release:
        run([sys.executable, str(root / "system/scripts/release_check.py"), "--root", str(root)])
    print("Iron Agent smoke test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
