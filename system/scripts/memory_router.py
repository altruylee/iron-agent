"""Route a task through workspace/memory/index.json before reading memory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FALLBACK_INDEX = {
    "财务结算": [
        "workspace/memory/episodes/finance/settlement/INDEX.md",
        "workspace/memory/semantic/sops/finance-settlement.md",
    ],
    "用户注册": [
        "workspace/memory/episodes/user/registration/INDEX.md",
        "workspace/memory/semantic/sops/user-registration.md",
    ],
    "开发": [
        "packs/domain-agents/INDEX.md",
        "workspace/memory/episodes/development/INDEX.md",
    ],
}


def load_index(root: Path) -> dict[str, list[str]]:
    index_path = root / "workspace" / "memory" / "index.json"
    if not index_path.exists():
        return FALLBACK_INDEX
    data = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("workspace/memory/index.json must be an object")
    result: dict[str, list[str]] = {}
    for topic, paths in data.items():
        if isinstance(paths, list):
            result[str(topic)] = [str(path) for path in paths]
    return result


def score_topic(task: str, topic: str) -> int:
    lowered = task.lower()
    score = 0
    if topic.lower() in lowered:
        score += 10
    for token in topic.lower().replace("-", " ").split():
        if token and token in lowered:
            score += 2
    for char in topic:
        if "\u4e00" <= char <= "\u9fff" and char in task:
            score += 1
    return score


def route(root: Path, task: str, limit: int = 5, include_cold: bool = False) -> list[str]:
    index = load_index(root)
    ranked = sorted(
        ((topic, score_topic(task, topic), paths) for topic, paths in index.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    matches: list[str] = []
    for _topic, score, paths in ranked:
        if score < 2:
            continue
        for item in paths:
            if not include_cold and "/cold/" in item.replace("\\", "/"):
                continue
            if (root / item).exists():
                matches.append(item)
            if len(matches) >= limit:
                return list(dict.fromkeys(matches))
    return list(dict.fromkeys(matches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--task", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--include-cold", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    paths = route(root, args.task, limit=args.limit, include_cold=args.include_cold)
    if args.json:
        print(json.dumps({"paths": paths, "matched": bool(paths)}, ensure_ascii=False, indent=2))
        return 0
    if not paths:
        print("[未命中：按新内容正常处理]")
        return 0
    for item in paths:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
