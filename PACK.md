# Iron Agent Pack

## Directory

- [Purpose](#purpose)
- [Four Stages](#four-stages)
- [Install Surface](#install-surface)
- [Extension Surface](#extension-surface)
- [Release Surface](#release-surface)

## Purpose

Iron Agent Pack is a Codex-oriented local workspace package. It gives Codex a
stable place to store user context, domain knowledge, task logs, memories,
skills, and maintenance state.

## Four Stages

| Stage | What exists |
|---|---|
| Personal usable pack | Installers, initial setup, Codex global skill, permissions, logs, memory |
| Domain agent packs | `packs/domain-agents/` reserved for user-created field agents |
| Self-evolution | Memory maintenance, skill installation, repeated-workflow improvement |
| Distribution | `manifest.json`, installers, pack overview, health check |

## Install Surface

- Windows: `install.ps1`
- Cross-platform Python: `install.py`
- Optional Codex entrypoint: `codex-global-skill/SKILL.md`
- No external scheduler or automation is created by the installer.

## Extension Surface

Users should put field-specific agents, prompts, workflows, and pack notes under:

```text
packs/domain-agents/
```

Each domain agent should include a Markdown entry with `## Directory`.

## Release Surface

- Public overview: `README.md`
- Security policy: `SECURITY.md`
- Contribution guide: `CONTRIBUTING.md`
- Release notes: `CHANGELOG.md`
- License: `LICENSE`
- Cleanup: `system/scripts/release_cleanup.py`
- Release check: `system/scripts/release_check.py`
