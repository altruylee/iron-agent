# Engineering Package Skill

Use this skill to integrate repo-level or engineering-level packages such as
GitHub projects, multi-file skill packs, tool bundles, templates, or domain
agent collections. Do not treat these as single Markdown skills.

## Directory

- [Read Path From Here](#read-path-from-here)
- [Source Policy](#source-policy)
- [Integration Model](#integration-model)
- [Use Decision](#use-decision)
- [Process](#process)
- [Risk Policy](#risk-policy)

## Read Path From Here

| Need | Next file |
|---|---|
| Package analyzer | `system/scripts/analyze_package.py` |
| Package staging | `system/scripts/stage_package.py` |
| Package registry | `workspace/meta/package-registry.json` |
| Staged packages | `tools/packages/` |
| Domain agents | `packs/domain-agents/INDEX.md` |
| Skill installer | `system/skills/skill-installation.md` |
| Skill audit | `system/scripts/audit_skill.py` |

## Source Policy

Prefer a user-provided source:

- local cloned repo,
- local extracted folder,
- GitHub URL,
- archive path.

If the user provides only a package name, ask for the source first. Search the
web only after the user agrees. Network lookup or cloning is P2.

## Integration Model

Classify the package as one of:

- `skill_pack`: contains `SKILL.md`, `skills/`, or domain-specific agent instructions.
- `tool_package`: contains executable scripts, code, CLIs, or dependencies.
- `template_pack`: contains reusable templates, prompts, or examples.
- `knowledge_pack`: contains reference docs, notes, frameworks, or wiki-like content.
- `mixed_package`: combines several of the above.

Default placement:

- Stage full repo under `tools/packages/{slug}/`.
- Register metadata in `workspace/meta/package-registry.json`.
- Import domain-facing instructions to `packs/domain-agents/{domain}/` when useful.
- Promote to `system/skills/` only after audit and user confirmation.

## Use Decision

Codex may decide to use a registered package when:

- the user's task matches its detected domains or trigger keywords,
- the package has no unresolved high-risk audit finding,
- the package's registry status is `enabled`,
- using it is narrower than searching the full workspace or inventing a new workflow.

If uncertain, mention the matching package and ask before using it.

## Process

1. Get source from user. If source is a Git URL, ask before cloning.
2. Stage source under `tools/packages/{slug}/`:

```bash
python system/scripts/stage_package.py --root . --source {path-or-url}
```

3. Run:

```bash
python system/scripts/analyze_package.py --root . --source tools/packages/{slug}
```

4. Review `workspace/meta/package-registry.json`.
5. Run `audit_skill.py` against any candidate `SKILL.md` or agent Markdown.
6. If low risk, enable package in registry.
7. If medium risk, ask user before enabling.
8. If high risk, keep disabled and explain why.
9. Log the result.

## Risk Policy

- Low: Markdown-only references, templates, static examples.
- Medium: scripts, package managers, network use, local file writes.
- High: destructive commands, credential handling, persistence, scheduled tasks, remote-code execution, approval bypass.

Do not execute package scripts during analysis. Analyze first, run only after
user confirmation and risk review.
