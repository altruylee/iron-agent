"""Audit a proposed Iron Agent skill before installation."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path


TZ = timezone(timedelta(hours=8))

HIGH_PATTERNS = [
    r"Remove-Item\s+.*(-Recurse|-Force)",
    r"\brm\s+-rf\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\b",
    r"Invoke-Expression|\biex\b",
    r"curl\b.*\|\s*(bash|sh|powershell)",
    r"Invoke-WebRequest\b.*\|\s*Invoke-Expression",
    r"Start-Process\b.*-Verb\s+RunAs",
    r"Set-ExecutionPolicy",
    r"Register-ScheduledTask|schtasks\b",
    r"(send|upload|post|exfiltrate|print|echo|write|store|save).{0,50}(password|secret|token|api[_-]?key|private key|seed phrase)",
]

MEDIUM_PATTERNS = [
    r"\bpip\s+install\b",
    r"\bnpm\s+install\b|\bnpm\s+i\b",
    r"\buv\s+pip\s+install\b",
    r"Invoke-WebRequest|\bcurl\b|\bwget\b",
    r"\bStart-Process\b",
    r"\bpython\b.*\.py",
    r"\bnode\b.*\.js",
    r"\bMove-Item\b|\bCopy-Item\b",
    r"\bRemove-Item\b",
]


def slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return value.strip("-") or "skill"


def find_skill_files(source: Path) -> list[Path]:
    if source.is_file() and source.suffix.lower() == ".md":
        return [source]
    if source.is_dir():
        skill = source / "SKILL.md"
        if skill.exists():
            return [skill]
        return sorted(source.rglob("*.md"))
    return []


def has_frontmatter(text: str) -> bool:
    return text.startswith("---") and "name:" in text[:500] and "description:" in text[:1000]


def scan_text(text: str) -> tuple[list[str], list[str]]:
    high: list[str] = []
    medium: list[str] = []
    for pattern in HIGH_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            high.append(pattern)
    for pattern in MEDIUM_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            medium.append(pattern)
    return high, medium


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    source = Path(args.source).expanduser().resolve()
    report_dir = root / "output" / "skill-audits"
    report_dir.mkdir(parents=True, exist_ok=True)

    findings: list[dict] = []
    files = find_skill_files(source)
    if not source.exists():
        findings.append({"severity": "high", "message": f"Source does not exist: {source}"})
    elif not files:
        findings.append({"severity": "high", "message": "No Markdown skill file found"})

    for file_path in files:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        rel = str(file_path)
        if file_path.name == "SKILL.md" and not has_frontmatter(text):
            findings.append({"severity": "medium", "file": rel, "message": "SKILL.md lacks expected name/description frontmatter"})
        if "## Directory" not in text:
            findings.append({"severity": "low", "file": rel, "message": "Markdown file has no ## Directory section"})
        high, medium = scan_text(text)
        findings.extend({"severity": "high", "file": rel, "message": f"Matched high-risk pattern: {p}"} for p in high)
        findings.extend({"severity": "medium", "file": rel, "message": f"Matched medium-risk pattern: {p}"} for p in medium)

    if any(item["severity"] == "high" for item in findings):
        risk = "high"
    elif any(item["severity"] == "medium" for item in findings):
        risk = "medium"
    else:
        risk = "low"

    result = {
        "time": datetime.now(TZ).isoformat(timespec="seconds"),
        "source": str(source),
        "risk": risk,
        "files_scanned": [str(path) for path in files],
        "findings": findings,
    }

    report_path = report_dir / f"{datetime.now(TZ).strftime('%Y%m%d-%H%M%S')}-{slug(source.name)}.json"
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"risk={risk}")
        print(f"report={report_path}")
        for item in findings:
            print(f"[{item['severity']}] {item.get('file', '')} {item['message']}")

    return 2 if risk == "high" else 1 if risk == "medium" else 0


if __name__ == "__main__":
    raise SystemExit(main())
