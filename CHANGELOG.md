# Changelog

## Directory

- [0.1.0](#010)
- [0.3.8](#038)
- [0.3.7](#037)
- [0.3.6](#036)
- [0.3.5](#035)
- [0.3.4](#034)
- [0.3.3](#033)
- [0.3.1](#031)
- [0.3.2](#032)
- [0.3.0](#030)
- [0.2.0](#020)

## 0.3.8

- Added `iron update` for one-command workspace upgrades that preserve accumulated user data.
- Added top-level clarification-before-execution protocol for Codex, Claude Code, and WorkBuddy.
- Added daily maintenance upgrade reminders and required HTML report links.

## 0.3.7

- Removed editor-specific compatibility files.
- Kept the core adapter surface focused on Codex, Claude Code, and WorkBuddy.
- Added `WORKBUDDY.md` and the WorkBuddy adapter template.

## 0.3.6

- Added the Memory Observatory static HTML report for daily maintenance.
- Added `output/maintenance/index.html`, daily HTML reports, and `maintenance-history.json` generation.
- Added long-term token savings trend data for maintenance reports.

## 0.3.5

- Simplified README installation instructions.
- Removed domain-specific starter memory, examples, and default routing.
- Replaced the default SOP seed with a generic task-review workflow.

## 0.3.4

- Fixed install flow so file copy keeps `install_status: 0` until first-use onboarding is completed.
- Stopped `iron doctor --fix` and `iron quickstart` from silently marking installation complete.
- Added `OPEN_ME_FIRST.md` and clearer post-install guidance for Codex workspace selection.

## 0.3.3

- Added `iron automation install/status` for silent adapter setup and daily background maintenance.
- Added Claude Code hook support and silent automation documentation.

## 0.3.2

- Clarified Iron Agent as a prompt/rule/SOP overlay for daily model use.
- Changed memory routing misses to normal non-error output so agents continue as new content.
- Added daily-use model documentation.

## 0.3.1

- Added installable agent adapter files.
- Added adapter list/install/doctor commands.
- Added adapter documentation and root rule files.

## 0.3.0

- Added local offline Web UI via `iron web`.
- Added interactive evolution candidate preview and batch apply support.
- Added starter packs for developer, researcher, PM, and writer workflows.
- Added formal domain agent template and `iron agent new`.
- Added evolution threshold config and `iron config`.
- Added wiki/memory boundary documentation and move commands.
- Added machine-routed memory index, hot/warm/cold memory tiers, and low-token index slimming checks.
- Added initial agent adapter support.
- Clarified daily use model: route first, overlay on hit, normal conversation on miss, nightly organization and user notification.

## 0.2.0

- Added installable `iron` CLI package.
- Added `iron init`, `check`, `doctor`, `report`, `clean`, `memory`, `task`, `evolve`, `quickstart`, and `backup` commands.
- Added manifest-backed required file validation.
- Added automatic `install_status` maintenance during CLI initialization and doctor repair.
- Added `QUICKSTART.md`, troubleshooting docs, CI example, and end-to-end demo assets.

## 0.1.0

- Initial public package structure.
- Low-token directory-first execution protocol.
- Layered memory model.
- Domain agent import and runtime routing.
- Optional Windows preflight and Codex shadow review automation.
- Release cleanup and release check scripts.
