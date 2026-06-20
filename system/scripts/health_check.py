"""Check that the Iron Agent workspace has its required files and folders."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED = [
    "AGENTS.md",
    "CLAUDE.md",
    "WORKBUDDY.md",
    "README.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "LICENSE",
    "PACK.md",
    "manifest.json",
    "install.py",
    "install.ps1",
    "codex-global-skill/SKILL.md",
    "adapters/claude/CLAUDE.md",
    "adapters/workbuddy/WORKBUDDY.md",
    "packs/domain-agents/INDEX.md",
    "workspace/workspace-config.md",
    "workspace/meta/active-context.md",
    "workspace/meta/friction-log.md",
    "workspace/meta/memory.md",
    "workspace/meta/task-log.jsonl",
    "system/skills/initial-install.md",
    "system/skills/codex-agent.md",
    "system/skills/codex-automation.md",
    "system/skills/daily-maintenance.md",
    "system/skills/domain-agent-import.md",
    "system/skills/memory-maintenance.md",
    "system/skills/research.md",
    "system/skills/skill-installation.md",
    "system/skills/engineering-package.md",
    "system/skills/backup-restore.md",
    "system/skills/evolution.md",
    "system/skills/update-core.md",
    "system/scripts/audit_skill.py",
    "system/scripts/analyze_package.py",
    "system/scripts/backup_workspace.py",
    "system/scripts/evolution_report.py",
    "system/scripts/install_skill.py",
    "system/scripts/import_domain_agent.py",
    "system/scripts/memory_router.py",
    "system/scripts/memory_index_maintenance.py",
    "system/scripts/release_check.py",
    "system/scripts/release_cleanup.py",
    "system/scripts/restore_workspace.py",
    "system/scripts/shadow_reviewer.py",
    "system/scripts/stage_package.py",
    "system/scripts/structure_integrity.py",
    "system/scripts/test_pack.py",
    "system/scripts/update_core.py",
    "system/scripts/daily_maintenance.py",
    "system/scripts/domain_agent_router.py",
    "system/scripts/install_windows_task.ps1",
    "system/prompts/codex-shadow-maintenance.md",
    "config/maintenance.json",
    "config/user-profile.template.json",
    "config/automation.template.json",
    "config/privacy-policy.md",
    "examples/development-agent.md",
    "examples/task-review-shadow-review.md",
    "examples/user-registration-sop.md",
    "workspace/memory/INDEX.md",
    "workspace/memory/index.json",
    "workspace/memory/hot/INDEX.md",
    "workspace/memory/warm/INDEX.md",
    "workspace/memory/cold/INDEX.md",
    "workspace/memory/short-term/INDEX.md",
    "workspace/memory/episodes/INDEX.md",
    "workspace/memory/episodes/workflow/INDEX.md",
    "workspace/memory/episodes/workflow/task-review/INDEX.md",
    "workspace/memory/episodes/user/INDEX.md",
    "workspace/memory/episodes/user/registration/INDEX.md",
    "workspace/memory/episodes/user-registration/INDEX.md",
    "workspace/memory/episodes/development/INDEX.md",
    "workspace/memory/semantic/INDEX.md",
    "workspace/memory/semantic/sops/INDEX.md",
    "workspace/memory/semantic/sops/task-review.md",
    "workspace/memory/semantic/sops/user-registration.md",
    "workspace/memory/shadow-review/INDEX.md",
    "wiki/_schema.md",
    "inbox",
    "output",
    "watchlists",
    "hypotheses",
    "tools/packages",
    "backups",
    "workspace/memory/short-term",
    "workspace/memory/episodes",
    "workspace/memory/semantic/sops",
    "workspace/memory/shadow-review",
    "wiki/raw",
    "wiki/sources",
    "wiki/entities",
    "wiki/concepts",
    "wiki/explorations",
    "examples",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    missing = [item for item in REQUIRED if not (root / item).exists()]
    if missing:
        print("Missing:")
        for item in missing:
            print(f"- {item}")
        return 1

    print("Iron Agent workspace OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
