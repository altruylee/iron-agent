"""Prepare or apply durable memory updates from task-log candidates."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SECTION_BY_CATEGORY = {
    "preference": "Preferences",
    "project_fact": "Project Facts",
    "procedure": "Procedures",
    "decision": "Decisions",
    "credential_hint": "Credential Hints",
}

KEYWORDS = {
    "credential_hint": [
        "api key",
        "apikey",
        "token",
        "credential",
        "secret",
        "env",
        "environment variable",
        "key is in",
        "密钥",
        "环境变量",
    ],
    "decision": [
        "must",
        "require",
        "never",
        "always",
        "confirm",
        "permission",
        "p3",
        "必须",
        "不要",
        "禁止",
        "确认",
        "权限",
    ],
    "procedure": [
        "when",
        "use",
        "run",
        "write",
        "workflow",
        "process",
        "default to",
        "先",
        "流程",
        "步骤",
        "默认",
        "执行",
        "写入",
    ],
    "preference": [
        "prefer",
        "style",
        "language",
        "answer",
        "output style",
        "偏好",
        "风格",
        "语言",
        "回答",
    ],
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def classify(item: str) -> str:
    lowered = item.lower()
    for category, words in KEYWORDS.items():
        if any(word in lowered for word in words):
            return category
    if re.search(r"[A-Za-z]:\\|/[^ ]+/", item):
        return "project_fact"
    return "project_fact"


def parse_task_log(log_path: Path) -> list[str]:
    candidates: list[str] = []
    if not log_path.exists():
        return candidates

    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        for item in entry.get("memory_candidates", []):
            item = str(item).strip().strip("-").strip()
            if item:
                candidates.append(item)
    return candidates


def collect_existing(memory_text: str) -> set[str]:
    existing: set[str] = set()
    for line in memory_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            existing.add(normalize(stripped[2:]))
    return existing


def group_candidates(candidates: list[str], existing: set[str], limit: int) -> dict[str, list[str]]:
    grouped = {section: [] for section in SECTION_BY_CATEGORY.values()}
    seen: set[str] = set()

    for item in candidates:
        key = normalize(item)
        if not key or key in existing or key in seen:
            continue
        seen.add(key)
        category = classify(item)
        section = SECTION_BY_CATEGORY[category]
        grouped[section].append(item)
        if sum(len(values) for values in grouped.values()) >= limit:
            break

    return grouped


def render_review(grouped: dict[str, list[str]]) -> str:
    lines = [
        "# Memory Maintenance Candidates",
        "",
        "Review these candidates before merging into `workspace/meta/memory.md`.",
        "Delete anything transient, speculative, duplicated, or sensitive.",
        "",
        "## Directory",
        "",
        "- [Preferences](#preferences)",
        "- [Project Facts](#project-facts)",
        "- [Procedures](#procedures)",
        "- [Decisions](#decisions)",
        "- [Credential Hints](#credential-hints)",
        "",
    ]
    for section in SECTION_BY_CATEGORY.values():
        lines.append(f"## {section}")
        lines.append("")
        items = grouped.get(section, [])
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- (none)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def append_to_memory(memory_path: Path, grouped: dict[str, list[str]]) -> int:
    text = memory_path.read_text(encoding="utf-8") if memory_path.exists() else "# Personal AI Memory\n"
    inserted = 0

    for section, items in grouped.items():
        useful = [item for item in items if item.strip()]
        if not useful:
            continue

        heading = f"## {section}"
        block = "\n".join(f"- {item}" for item in useful) + "\n"
        if heading not in text:
            text = text.rstrip() + f"\n\n{heading}\n\n{block}"
            inserted += len(useful)
            continue

        pattern = re.compile(rf"(^## {re.escape(section)}\n)", re.MULTILINE)
        match = pattern.search(text)
        if not match:
            continue
        insert_at = match.end()
        text = text[:insert_at] + "\n" + block + text[insert_at:]
        inserted += len(useful)

    memory_path.write_text(text, encoding="utf-8")
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", default="workspace/meta/memory-candidates.md")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    log_path = root / "workspace" / "meta" / "task-log.jsonl"
    memory_path = root / "workspace" / "meta" / "memory.md"
    output_path = root / args.output

    memory_text = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
    existing = collect_existing(memory_text)
    candidates = parse_task_log(log_path)
    grouped = group_candidates(candidates, existing, args.limit)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_review(grouped), encoding="utf-8")

    total = sum(len(values) for values in grouped.values())
    print(f"Prepared {total} memory candidates: {output_path}")

    if args.apply:
        inserted = append_to_memory(memory_path, grouped)
        print(f"Applied {inserted} memory entries: {memory_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
