"""Promote stable SOP candidates from async review files and memory candidates."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


TZ = timezone(timedelta(hours=8))

SOP_MARKERS = [
    "SOP",
    "workflow",
    "process",
    "procedure",
    "steps",
    "always",
    "must",
    "流程",
    "步骤",
    "标准操作",
    "固定下来",
    "复用",
    "必须",
]


def has_sop_signal(text: str) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in SOP_MARKERS)


def detect_target(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["任务复盘", "复盘", "workflow", "review"]):
        return "task-review.md"
    if any(word in lowered for word in ["用户注册", "注册", "registration", "onboarding"]):
        return "user-registration.md"
    return "captured-procedures.md"


def extract_bullets(text: str, limit: int = 20) -> list[str]:
    bullets: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("-", "*")) or re.match(r"^\d+[.)]\s+", line):
            clean = re.sub(r"^[-*\d.)\s]+", "", line).strip()
            if clean and len(clean) <= 240 and clean.lower() not in {"none", "(none)"}:
                bullets.append(clean)
        if len(bullets) >= limit:
            break
    return bullets


def section_bullets(text: str, section_names: set[str], limit: int = 40) -> list[str]:
    current = ""
    bullets: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip().lower()
            continue
        if current not in section_names:
            continue
        stripped = line.strip()
        if not stripped.startswith(("-", "*")):
            continue
        clean = re.sub(r"^[-*\s]+", "", stripped).strip()
        if clean and clean.lower() not in {"none", "(none)"} and len(clean) <= 240:
            bullets.append(clean)
        if len(bullets) >= limit:
            break
    return bullets


def ensure_sop_file(path: Path) -> None:
    if path.exists():
        return
    title = path.stem.replace("-", " ").title()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                "## Directory",
                "",
                "- [Purpose](#purpose)",
                "- [Procedures](#procedures)",
                "",
                "## Purpose",
                "",
                "Automatically promoted reusable procedures from daily maintenance.",
                "",
                "## Procedures",
                "",
            ]
        ),
        encoding="utf-8",
    )


def append_sop(sop_path: Path, source_name: str, bullets: list[str]) -> tuple[bool, int]:
    if not bullets:
        return False, 0
    ensure_sop_file(sop_path)
    text = sop_path.read_text(encoding="utf-8", errors="replace")
    existing = {line.strip().lower() for line in text.splitlines()}
    fresh = [item for item in bullets if f"- {item}".lower() not in existing]
    if not fresh:
        return False, 0
    stamp = datetime.now(TZ).date().isoformat()
    block = [
        "",
        f"### Promoted {stamp} from `{source_name}`",
        "",
        *[f"- {item}" for item in fresh],
        "",
    ]
    sop_path.write_text(text.rstrip() + "\n" + "\n".join(block), encoding="utf-8")
    return True, len(fresh)


def shrink_review_file(path: Path, target: str) -> None:
    body = [
        f"# Reviewed {path.stem}",
        "",
        "## Directory",
        "",
        "- [Status](#status)",
        "",
        "## Status",
        "",
        f"- Promoted to `../semantic/sops/{target}`.",
        "- Raw cache removed from active review path.",
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")


def promote_shadow_review(root: Path, sop_dir: Path) -> tuple[int, int]:
    review_dir = root / "workspace" / "memory" / "shadow-review"
    promoted_files = 0
    promoted_bullets = 0
    if not review_dir.exists():
        return promoted_files, promoted_bullets
    for path in review_dir.glob("*.md"):
        if path.name == "INDEX.md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not has_sop_signal(text):
            continue
        target = detect_target(text)
        bullets = extract_bullets(text)
        changed, count = append_sop(sop_dir / target, path.name, bullets)
        if changed:
            shrink_review_file(path, target)
            promoted_files += 1
            promoted_bullets += count
    return promoted_files, promoted_bullets


def promote_memory_candidates(root: Path, sop_dir: Path) -> tuple[int, int]:
    path = root / "workspace" / "meta" / "memory-candidates.md"
    if not path.exists():
        return 0, 0
    text = path.read_text(encoding="utf-8", errors="replace")
    procedure_items = section_bullets(text, {"procedures", "sop candidates"})
    promoted_files = 0
    promoted_bullets = 0
    grouped: dict[str, list[str]] = {}
    for item in procedure_items:
        if not has_sop_signal(item) and len(item) < 12:
            continue
        grouped.setdefault(detect_target(item), []).append(item)
    for target, bullets in grouped.items():
        changed, count = append_sop(sop_dir / target, "memory-candidates.md#Procedures", bullets)
        if changed:
            promoted_files += 1
            promoted_bullets += count
    return promoted_files, promoted_bullets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    sop_dir = root / "workspace" / "memory" / "semantic" / "sops"
    review_files, review_bullets = promote_shadow_review(root, sop_dir)
    candidate_files, candidate_bullets = promote_memory_candidates(root, sop_dir)
    promoted_files = review_files + candidate_files
    promoted_bullets = review_bullets + candidate_bullets

    print(f"Promoted SOP files: {promoted_files}")
    print(f"Promoted SOP bullets: {promoted_bullets}")
    print(f"Candidate SOP files: {candidate_files}")
    print(f"Candidate SOP bullets: {candidate_bullets}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
