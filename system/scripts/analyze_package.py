"""Analyze repo-level packages and register how Iron Agent should route them."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path


TZ = timezone(timedelta(hours=8))

DOMAIN_KEYWORDS = {
    "business": ["business", "customer", "growth", "metrics", "业务", "客户", "增长", "指标"],
    "coding": ["code", "python", "typescript", "javascript", "repo", "cli", "test", "代码", "开发"],
    "writing": ["writing", "article", "copy", "newsletter", "blog", "写作", "文章"],
    "research": ["research", "analysis", "source", "paper", "study", "研究", "分析"],
    "operations": ["ops", "automation", "monitor", "workflow", "dashboard", "自动化", "流程"],
}

RISK_PATTERNS = {
    "high": [
        r"\brm\s+-rf\b",
        r"Remove-Item\s+.*(-Recurse|-Force)",
        r"curl\b.*\|\s*(bash|sh|powershell)",
        r"Invoke-Expression|\biex\b",
        r"Register-ScheduledTask|schtasks\b",
        r"(send|upload|post|exfiltrate|print|echo|write|store|save).{0,50}(password|secret|token|api[_-]?key|private key)",
    ],
    "medium": [
        r"\bpip\s+install\b",
        r"\bnpm\s+(install|i)\b",
        r"Invoke-WebRequest|\bcurl\b|\bwget\b",
        r"\bpython\b.*\.py",
        r"\bnode\b.*\.js",
    ],
}


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip().lower()).strip("-") or "package"


def read_sample(files: list[Path], limit: int = 50000) -> str:
    chunks: list[str] = []
    total = 0
    for path in files:
        if total >= limit:
            break
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        chunks.append(text[: max(0, limit - total)])
        total += len(chunks[-1])
    return "\n".join(chunks)


def classify(files: list[Path]) -> str:
    names = [path.name.lower() for path in files]
    if "skill.md" in names or any("skills" in path.parts for path in files):
        if any(path.suffix in {".py", ".ps1", ".js", ".ts"} for path in files):
            return "mixed_package"
        return "skill_pack"
    if any(path.suffix in {".py", ".ps1", ".js", ".ts", ".sh"} for path in files):
        return "tool_package"
    if any("template" in str(path).lower() or "example" in str(path).lower() for path in files):
        return "template_pack"
    return "knowledge_pack"


def detect_domains(text: str) -> list[str]:
    lowered = text.lower()
    scored = []
    for domain, words in DOMAIN_KEYWORDS.items():
        score = sum(1 for word in words if word.lower() in lowered)
        if score:
            scored.append((domain, score))
    return [domain for domain, _ in sorted(scored, key=lambda item: item[1], reverse=True)] or ["general"]


def detect_risk(text: str) -> tuple[str, list[str]]:
    findings: list[str] = []
    risk = "low"
    for pattern in RISK_PATTERNS["high"]:
        if re.search(pattern, text, flags=re.IGNORECASE):
            findings.append(f"high:{pattern}")
            risk = "high"
    if risk != "high":
        for pattern in RISK_PATTERNS["medium"]:
            if re.search(pattern, text, flags=re.IGNORECASE):
                findings.append(f"medium:{pattern}")
                risk = "medium"
    return risk, findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source", required=True)
    parser.add_argument("--name", default="")
    parser.add_argument("--enable", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        raise SystemExit(f"Source must be an existing directory: {source}")

    files = [path for path in source.rglob("*") if path.is_file()]
    md_files = [path for path in files if path.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml"}]
    sample = read_sample(md_files or files)
    package_type = classify(files)
    domains = detect_domains(sample + " " + source.name)
    risk, findings = detect_risk(sample)
    package_name = slug(args.name or source.name)

    entry = {
        "name": package_name,
        "source": str(source),
        "registered_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "status": "enabled" if args.enable and risk == "low" else "disabled" if risk == "high" else "review",
        "type": package_type,
        "domains": domains,
        "risk": risk,
        "findings": findings,
        "entry_files": [str(path.relative_to(source)) for path in files if path.name.lower() in {"skill.md", "agent.md", "readme.md", "agents.md"}][:20],
        "use_when": [
            f"Use for {domain} tasks when the user asks for package-specific workflow or matching domain analysis."
            for domain in domains
        ],
    }

    registry_path = root / "workspace" / "meta" / "package-registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            registry = {"packages": []}
    else:
        registry = {"packages": []}

    registry["packages"] = [item for item in registry.get("packages", []) if item.get("name") != package_name]
    registry["packages"].append(entry)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(entry, ensure_ascii=False, indent=2))
    print(f"registry={registry_path}")
    return 2 if risk == "high" else 1 if risk == "medium" else 0


if __name__ == "__main__":
    raise SystemExit(main())
