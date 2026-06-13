"""Find active domain agents that should be loaded for a task."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DOMAIN_KEYWORDS = {
    "development": ["code", "repo", "bug", "test", "refactor", "开发", "代码", "编程", "仓库", "测试", "重构"],
    "investing": ["stock", "finance", "market", "投资", "股票", "投研", "财报"],
    "writing": ["write", "draft", "article", "写作", "文章", "文案"],
    "research": ["research", "source", "paper", "研究", "资料", "分析"],
    "operations": ["workflow", "automation", "ops", "流程", "自动化", "运营"],
}


def registered_domains(root: Path) -> list[str]:
    base = root / "packs" / "domain-agents"
    if not base.exists():
        return []
    return sorted(
        path.name for path in base.iterdir() if path.is_dir() and (path / "RUNTIME.md").exists()
    )


def match_domains(root: Path, task: str) -> list[str]:
    lowered = task.lower()
    matches: list[str] = []
    for domain in registered_domains(root):
        words = DOMAIN_KEYWORDS.get(domain, [domain])
        if domain in lowered or any(word.lower() in lowered for word in words):
            matches.append(domain)
    return matches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    matches = match_domains(root, args.task)
    if not matches:
        print("No matching domain agent")
        return 0
    for domain in matches:
        runtime = root / "packs" / "domain-agents" / domain / "RUNTIME.md"
        print(runtime.relative_to(root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
