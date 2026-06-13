"""Promote stable SOP candidates from async review files."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


TZ = timezone(timedelta(hours=8))

SOP_MARKERS = ["SOP", "流程", "步骤", "标准操作", "固定下来", "复用", "always", "must", "必须"]


def has_sop_signal(text: str) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in SOP_MARKERS)


def detect_target(text: str) -> str | None:
    lowered = text.lower()
    if any(word in lowered for word in ["财务结算", "结算", "对账", "finance", "settlement"]):
        return "finance-settlement.md"
    if any(word in lowered for word in ["用户注册", "注册", "registration", "onboarding"]):
        return "user-registration.md"
    return None


def extract_bullets(text: str, limit: int = 12) -> list[str]:
    bullets: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("-", "*")) or re.match(r"^\d+[.)]\s+", line):
            clean = re.sub(r"^[-*\d.)\s]+", "", line).strip()
            if clean and len(clean) <= 220:
                bullets.append(clean)
        if len(bullets) >= limit:
            break
    return bullets


def append_sop(sop_path: Path, source_name: str, bullets: list[str]) -> bool:
    if not bullets:
        return False
    text = sop_path.read_text(encoding="utf-8") if sop_path.exists() else ""
    existing = {line.strip().lower() for line in text.splitlines()}
    fresh = [item for item in bullets if f"- {item}".lower() not in existing]
    if not fresh:
        return False
    stamp = datetime.now(TZ).date().isoformat()
    block = [
        "",
        f"### Promoted {stamp} from `{source_name}`",
        "",
        *[f"- {item}" for item in fresh],
        "",
    ]
    sop_path.write_text(text.rstrip() + "\n".join(block), encoding="utf-8")
    return True


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    review_dir = root / "workspace" / "memory" / "shadow-review"
    sop_dir = root / "workspace" / "memory" / "semantic" / "sops"
    promoted = 0

    for path in review_dir.glob("*.md"):
        if path.name == "INDEX.md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not has_sop_signal(text):
            continue
        target = detect_target(text)
        if not target:
            continue
        bullets = extract_bullets(text)
        if append_sop(sop_dir / target, path.name, bullets):
            shrink_review_file(path, target)
            promoted += 1

    print(f"Promoted SOP files: {promoted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
