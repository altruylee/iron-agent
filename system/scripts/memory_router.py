"""Route a task to the smallest relevant memory path."""

from __future__ import annotations

import argparse
from pathlib import Path


TOPICS = {
    "财务结算": {
        "keywords": ["财务结算", "结算", "对账", "账期", "付款", "收款", "发票", "finance", "settlement"],
        "paths": [
            "workspace/memory/episodes/finance/INDEX.md",
            "workspace/memory/semantic/sops/finance-settlement.md",
        ],
    },
    "用户注册": {
        "keywords": ["用户注册", "注册", "登录", "开户", "验证码", "账号", "onboarding", "registration"],
        "paths": [
            "workspace/memory/episodes/user-registration/INDEX.md",
            "workspace/memory/semantic/sops/user-registration.md",
        ],
    },
    "开发": {
        "keywords": ["开发", "代码", "bug", "测试", "重构", "repo", "code", "test", "refactor"],
        "paths": [
            "packs/domain-agents/INDEX.md",
            "workspace/memory/episodes/development/INDEX.md",
        ],
    },
}


def route(task: str) -> list[str]:
    lowered = task.lower()
    matches: list[str] = []
    for spec in TOPICS.values():
        if any(word.lower() in lowered for word in spec["keywords"]):
            matches.extend(spec["paths"])
    return list(dict.fromkeys(matches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    paths = route(args.task)
    if not paths:
        print("[缺少前置条件：请补充具体业务模块或主题]")
        return 2
    for item in paths:
        if (root / item).exists():
            print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
