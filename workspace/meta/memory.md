# Personal AI Memory

This file stores durable memory. Do not use it as a chat transcript or task log.

## Directory

- [Preferences](#preferences)
- [Project Facts](#project-facts)
- [Procedures](#procedures)
- [Decisions](#decisions)
- [Credential Hints](#credential-hints)

## Read Path From Here

- For execution rules, read `system/skills/codex-agent.md`.
- For topic memory, read `workspace/memory/INDEX.md` first.
- For recent continuation state, read `workspace/meta/active-context.md`.
- For task audit history, read `workspace/meta/task-log.jsonl` only when needed.

## Preferences

- Default to Chinese unless the user requests another language.
- Give the conclusion first, then evidence and next actions.
- Keep Chinese requests as Chinese; add English keywords only for search, docs, code identifiers, library names, or exact error matching.
- Keep requests and responses concise, precise, and task-relevant; avoid emotional wording and unrelated content to reduce token use.
- Treat concise requests plus tree-style directory navigation as Iron Agent's first principle.
- Do not read all memory every round; route by `workspace/memory/INDEX.md`.

## Project Facts

- Iron Agent workspace path is the installed folder that contains `AGENTS.md`.

## Procedures

- Iron Agent uses AGENTS.md Installation State install_status to gate first-use setup

- Ingest raw material into `wiki/raw/`, then create a single-source summary in `wiki/sources/`.
- Write task outputs to `output/` first. Move only durable knowledge into `wiki/`.
- For research, check local `wiki/` before external search.
- Record completed tasks in `workspace/meta/task-log.jsonl`.
- After updating Markdown, memory, skills, or navigation, preserve `## Directory` sections and run `system/scripts/structure_integrity.py`.
- When a user provides an existing agent file, import it with `system/scripts/import_domain_agent.py`; future matching tasks must load its generated `RUNTIME.md` and `RULES.md`.
- Promote stable SOPs to `workspace/memory/semantic/sops/` asynchronously, then clear or shrink related cache.

## Decisions

- P3 operations require explicit user confirmation.
- Secrets must not be written into the workspace.
- Every durable update must keep local links and read paths current.
- Domain agents are active runtime overlays, not passive references, after import.
- Live conversation must not trigger high-token memory consolidation or self-evolution unless explicitly requested.

## Credential Hints

- Store API keys in environment variables or local ignored config, not in repo files.
