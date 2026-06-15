"""Import a user-provided agent file as an enforceable domain agent."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


TZ = timezone(timedelta(hours=8))

DOMAIN_KEYWORDS = {
    "development": [
        "code",
        "coding",
        "programming",
        "developer",
        "repo",
        "bug",
        "test",
        "refactor",
        "python",
        "javascript",
        "typescript",
        "代码",
        "开发",
        "编程",
        "仓库",
        "测试",
        "重构",
    ],
    "business": ["business", "customer", "growth", "metrics", "业务", "客户", "增长", "指标"],
    "writing": ["write", "article", "newsletter", "copywriting", "blog", "写作", "文章", "文案"],
    "research": ["research", "paper", "analysis", "source", "citation", "研究", "分析", "资料"],
    "operations": ["ops", "operation", "workflow", "automation", "dashboard", "运营", "自动化", "流程"],
}

RULE_MARKERS = [
    "must",
    "required",
    "mandatory",
    "always",
    "never",
    "do not",
    "should",
    "必须",
    "强制",
    "一定",
    "总是",
    "禁止",
    "不得",
    "不要",
    "需要",
    "应该",
]


def slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip().lower())
    return value.strip("-") or "general"


def infer_domain(text: str, fallback: str) -> str:
    lowered = text.lower()
    scores = {
        domain: sum(1 for word in words if word.lower() in lowered)
        for domain, words in DOMAIN_KEYWORDS.items()
    }
    best, score = max(scores.items(), key=lambda item: item[1])
    return best if score > 0 else slug(fallback)


def ensure_directory_section(title: str, body: str) -> str:
    if "## Directory" in body:
        return body
    return (
        f"# {title}\n\n"
        "## Directory\n\n"
        "- [Source](#source)\n"
        "- [Imported Agent](#imported-agent)\n\n"
        "## Source\n\n"
        "Original file content follows.\n\n"
        "## Imported Agent\n\n"
        f"{body.rstrip()}\n"
    )


def extract_rules(text: str, limit: int = 80) -> list[str]:
    rules: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or len(line) < 6 or len(line) > 260:
            continue
        lowered = line.lower()
        if any(marker in lowered for marker in RULE_MARKERS):
            clean = re.sub(r"^[-*+\d.)\s]+", "", line).strip()
            if clean and clean not in seen:
                rules.append(clean)
                seen.add(clean)
        if len(rules) >= limit:
            break
    if not rules:
        rules.append("Read `AGENT.md` before matching domain tasks and apply its reusable workflow rules.")
    return rules


def write_rules(target_dir: Path, domain: str, rules: list[str]) -> None:
    lines = [
        f"# {domain.title()} Domain Rules",
        "",
        "## Directory",
        "",
        "- [Purpose](#purpose)",
        "- [Mandatory Rules](#mandatory-rules)",
        "- [Source Agent](#source-agent)",
        "",
        "## Purpose",
        "",
        "This file extracts enforceable rules from the imported domain agent.",
        "",
        "## Mandatory Rules",
        "",
    ]
    lines.extend(f"- {rule}" for rule in rules)
    lines += [
        "",
        "## Source Agent",
        "",
        "- Full imported source: `AGENT.md`",
        "",
    ]
    (target_dir / "RULES.md").write_text("\n".join(lines), encoding="utf-8")


def write_runtime(target_dir: Path, domain: str) -> None:
    content = f"""# {domain.title()} Domain Runtime

## Directory

- [When To Load](#when-to-load)
- [Mandatory Preflight](#mandatory-preflight)
- [Runtime Contract](#runtime-contract)
- [Files](#files)

## When To Load

Load this runtime before any task that matches the `{domain}` domain, its
trigger terms, or the user's explicit instruction to use this domain agent.

## Mandatory Preflight

- Read `RULES.md`.
- Read `AGENT.md` when the task is non-trivial or rules are ambiguous.
- Apply all mandatory rules that do not conflict with the user's latest request.
- If a mandatory rule conflicts with the user's request, stop and ask before continuing.
- Record this domain agent in the task log when task logging is performed.

## Runtime Contract

- Keep the user's request concise and preserve the original language.
- Use the shortest read path that reaches the relevant project files.
- Do not ignore this domain runtime for matching tasks unless the user explicitly disables it.

## Files

- Source agent: `AGENT.md`
- Extracted rules: `RULES.md`
- Import metadata: `source-info.json`
"""
    (target_dir / "RUNTIME.md").write_text(content, encoding="utf-8")


def update_index(root: Path, domain: str) -> None:
    index = root / "packs" / "domain-agents" / "INDEX.md"
    text = index.read_text(encoding="utf-8")
    row = f"| {domain} | `{domain}/RUNTIME.md` | `{domain}/RULES.md` | `{domain}/AGENT.md` | active |"
    if row in text:
        return
    heading = "## Registered Domain Agents"
    if heading not in text:
        insert = (
            "\n## Registered Domain Agents\n\n"
            "| Domain | Runtime | Rules | Source Agent | Status |\n"
            "|---|---|---|---|---|\n"
            f"{row}\n"
        )
        marker = "\n## Recommended Layout"
        text = text.replace(marker, insert + marker)
    else:
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if line.startswith("|---|") and idx > 0 and "Domain" in lines[idx - 1]:
                lines.insert(idx + 1, row)
                break
        text = "\n".join(lines) + "\n"
    index.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source", required=True)
    parser.add_argument("--domain", default="")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise SystemExit(f"Source must be an existing file: {source}")

    text = source.read_text(encoding="utf-8", errors="replace")
    domain = slug(args.domain) if args.domain else infer_domain(text, source.stem)
    target_dir = root / "packs" / "domain-agents" / domain
    target_file = target_dir / "AGENT.md"

    if target_file.exists() and not args.overwrite:
        raise SystemExit(f"Target already exists: {target_file}. Use --overwrite to replace.")

    target_dir.mkdir(parents=True, exist_ok=True)
    target_file.write_text(ensure_directory_section(f"{domain.title()} Domain Agent", text), encoding="utf-8")
    rules = extract_rules(text)
    write_rules(target_dir, domain, rules)
    write_runtime(target_dir, domain)
    update_index(root, domain)

    info = {
        "imported_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "source": str(source),
        "domain": domain,
        "target": str(target_file),
        "runtime": str(target_dir / "RUNTIME.md"),
        "rules": str(target_dir / "RULES.md"),
        "status": "active",
        "note": "Imported as an enforceable domain agent. Audit before promoting to system skills.",
    }
    (target_dir / "source-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Imported domain agent: {target_file}")
    print(f"Runtime: {target_dir / 'RUNTIME.md'}")
    print(f"Rules: {target_dir / 'RULES.md'}")
    print(f"Domain: {domain}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
