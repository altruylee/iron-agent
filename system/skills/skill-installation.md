# Skill Installation Skill

Use this skill when Iron Agent needs to install, import, update, or discover a
workspace skill. Prefer user-provided sources. If the user does not provide a
source, ask for one first; only search externally after the user agrees.

## Directory

- [Read Path From Here](#read-path-from-here)
- [Source Priority](#source-priority)
- [Security Audit](#security-audit)
- [Install Process](#install-process)
- [Risk Policy](#risk-policy)
- [Verification](#verification)

## Read Path From Here

| Need | Next file |
|---|---|
| Workspace execution rules | `system/skills/codex-agent.md` |
| Skill audit script | `system/scripts/audit_skill.py` |
| Skill install script | `system/scripts/install_skill.py` |
| Installed skills | `system/skills/` |
| Audit reports | `output/skill-audits/` |
| Task log | `workspace/meta/task-log.jsonl` |

## Source Priority

Ask the user for a skill source before searching.

Accepted sources:

- a local `.md` skill file,
- a local folder containing `SKILL.md`,
- a local archive already extracted by the user,
- a Git URL or web URL only after the user explicitly allows external lookup.

If no source is provided:

1. Ask for a source path or URL.
2. If the user asks Iron Agent to search, classify it as P2.
3. Prefer official or primary sources.
4. Do not install anything found online before audit and user confirmation.

## Security Audit

Before installing, run:

```bash
python system/scripts/audit_skill.py --root . --source {source}
```

The audit checks for:

- missing `SKILL.md` or malformed frontmatter,
- commands that delete, overwrite, move, download, or execute remote code,
- credential or secret handling,
- network calls,
- package installs,
- scheduled tasks or persistence,
- instructions that bypass approvals,
- suspicious encoded payloads or obfuscation.

Write audit reports to `output/skill-audits/`.

## Install Process

1. Get the source from the user.
2. Run the security audit.
3. Read the audit report.
4. If risk is high, stop and explain the risk.
5. If risk is medium, ask for confirmation before installing.
6. If risk is low, install with:

```bash
python system/scripts/install_skill.py --root . --source {source}
```

7. Update `workspace/meta/task-log.jsonl`.
8. Add a short active-context entry if the installed skill needs follow-up.

## Risk Policy

- Low risk: markdown-only instructions, no privileged operations.
- Medium risk: network calls, dependency installs, local script execution, or write operations.
- High risk: destructive commands, credential exfiltration, persistence, auto-run hooks, approval bypass, remote-code execution.

High-risk skills require explicit user approval and should normally not be
installed. Tell the user what to remove or sandbox before retrying.

## Verification

After install:

1. Confirm the installed file exists in `system/skills/`.
2. Confirm every installed Markdown file has `## Directory`.
3. Run `system/scripts/health_check.py`.
4. Log the install result.

