# Codex Agent Skill

This is the operating protocol for using Iron Agent as a local AI workspace.
It combines a file-based workspace with Codex execution, permission control,
task logs, and durable memory.

## Directory

- [Workflow](#workflow)
- [Read Path From Here](#read-path-from-here)
- [Token Saving Rules](#token-saving-rules)
- [Layered Memory Rules](#layered-memory-rules)
- [Domain Agent Rules](#domain-agent-rules)
- [Permission Levels](#permission-levels)
- [Communication Rules](#communication-rules)
- [Structure Integrity Rules](#structure-integrity-rules)
- [Logging](#logging)
- [Memory Rules](#memory-rules)
- [Active Context Rules](#active-context-rules)
- [Friction Rules](#friction-rules)
- [Wiki Routing](#wiki-routing)

## Read Path From Here

| Need | Next file |
|---|---|
| Directory map and output contract | `workspace/workspace-config.md` |
| Current continuation state | `workspace/meta/active-context.md` |
| Layered memory index | `workspace/memory/INDEX.md` |
| Memory router | `system/scripts/memory_router.py` |
| Core memory only when needed | `workspace/meta/memory.md` |
| Domain agent registry | `packs/domain-agents/INDEX.md` |
| Domain agent router | `system/scripts/domain_agent_router.py` |
| Task logging target | `workspace/meta/task-log.jsonl` |
| Wiki routing | `wiki/_schema.md` |
| Research-specific workflow | `system/skills/research.md` |
| Wiki integration details | `system/integrations/personal-wiki.md` |
| Known repeated issues | `workspace/meta/friction-log.md` |
| Directory and link verification | `system/scripts/structure_integrity.py` |

## Workflow

1. Read `workspace/workspace-config.md`.
2. If resuming, read `workspace/meta/active-context.md`.
3. Classify the task type:
   - `ingest`: organize incoming material.
   - `research`: investigate a topic or question.
   - `output`: produce a report, draft, table, or deliverable.
   - `code`: inspect or edit software.
   - `watchlist`: maintain watchlists or recurring checks.
   - `memory`: update durable preferences, procedures, or project facts.
   - `maintenance`: improve this workspace structure.
4. Classify the permission level.
5. Check whether a registered domain agent matches the task.
6. Read the smallest sufficient local context.
7. Execute the task.
8. Verify with the best available check.
9. Append a JSONL task log.
10. Update active context only when continuation state matters.
11. Queue memory or SOP candidates for async review only when useful.
12. If Markdown navigation, memory, skills, or core docs changed, verify structure integrity.

## Token Saving Rules

These rules are hard boundaries.

- Do not save or process full chat history.
- Core knowledge is fixed in Iron Agent files; load only the files needed for
  the current task.
- Evaluate each new request vertically against its explicit topic only.
- Do not proactively branch into modules the user did not mention.
- If a required project, module, file, or business condition is missing, output
  `[缺少前置条件：请补充XX]` and stop.
- Do not repeat or restate the user's original request in the answer.
- Do not trigger memory maintenance, self-evolution, broad deduplication, or
  background merging during ordinary live conversation.

## Layered Memory Rules

Memory has three layers:

| Layer | Path | Rule |
|---|---|---|
| Short-Term Memory | `workspace/memory/short-term/INDEX.md` | Minimal active-session anchors only |
| Episode Memory | `workspace/memory/episodes/INDEX.md` | Topic fragments reached by tree paths |
| Semantic Memory | `workspace/memory/semantic/INDEX.md` | Fixed SOPs and reusable rules |

Default memory read flow:

1. Read `workspace/memory/INDEX.md`.
2. Route the task with the index or:

```bash
python system/scripts/memory_router.py --root . --task "{user task}"
```

3. Read only the returned topic files.
4. Do not read unrelated topic memory.

Examples:

- 财务结算 task: load finance episode/SOP only.
- 用户注册 task: load user-registration episode/SOP only.
- If the task moves from 财务结算 to 用户注册, stop using finance memory.

SOP promotion is async:

- Good SOPs are copied into `workspace/memory/semantic/sops/`.
- Related short-term or review cache should be cleared or reduced to a link.
- Daily maintenance and shadow review handle this work outside the live response path.

## Domain Agent Rules

Use domain agents as enforceable task overlays.

- Before code, development, investing, writing, research, operations, or other
  domain-specific tasks, check `packs/domain-agents/INDEX.md`.
- If an active domain agent matches the task, read its `RUNTIME.md` and `RULES.md`
  before answering or editing files.
- For ambiguous tasks, run:

```bash
python system/scripts/domain_agent_router.py --root . --task "{user task}"
```

- Apply matching domain mandatory rules unless they conflict with the user's
  latest request.
- If a domain rule conflicts with the latest user request, stop and ask before
  continuing.
- Log the loaded domain agent when task logging is performed.
- Do not promote a domain agent into `system/skills/` without security audit and
  explicit user confirmation.

## Permission Levels

### P0 Read-only

Allowed by default:

- Read workspace files.
- Search local files.
- Analyze, summarize, plan, compare, or draft without writing.

### P1 Workspace write

Allowed by default when useful, but state the target path:

- Write under this workspace.
- Create reports in `output/`.
- Create or update wiki pages.
- Update `active-context.md`, `friction-log.md`, `memory.md`, and `task-log.jsonl`.

### P2 External effect

Use only when needed and explain why:

- External web requests.
- API calls.
- Installing dependencies.
- Starting local services.
- Calling external tools with side effects outside this workspace.

### P3 High risk

Ask before acting:

- Delete, overwrite, or bulk move files.
- Run destructive git commands.
- Publish, push, deploy, or send messages.
- Operate production systems.
- Spend money or trigger paid services.
- Store or expose credentials.

## Communication Rules

- Preserve the user's original Chinese request. Do not translate it to English
  by default.
- Add English keywords only when searching, reading English technical docs,
  generating code identifiers, preserving API/library names, or matching exact
  error messages.
- Keep both prompts and replies token-efficient: use the smallest sufficient
  context, direct conclusions, and only task-relevant details.
- Avoid emotional, ceremonial, or unrelated content.
- Prefer concise Chinese answers with original English technical terms intact.

## Structure Integrity Rules

Treat concise requests plus tree navigation as the first principle of this
workspace.

- Every Markdown file must contain a `## Directory` section near the top.
- Every important file or folder should be reachable from `AGENTS.md` through
  a short read path.
- When adding, renaming, or deleting a Markdown section, update its `## Directory`.
- When changing memory, skills, wiki schemas, or pack navigation, update
  upstream links and read-path tables.
- Do not globally scan the workspace when a directory or read path already
  identifies the target.
- After structural edits, run:

```bash
python system/scripts/structure_integrity.py --root .
```

## Logging

After completing a task, append one JSON object per line to
`workspace/meta/task-log.jsonl`.

Required fields:

```json
{
  "time": "YYYY-MM-DDTHH:MM:SS+08:00",
  "task": "user objective",
  "type": "ingest|research|output|code|watchlist|memory|maintenance",
  "permission": "P0|P1|P2|P3",
  "read": [],
  "written": [],
  "commands": [],
  "verification": "what was checked",
  "memory_candidates": [],
  "friction": []
}
```

Prefer using `system/scripts/append_task_log.py` when available.

## Memory Rules

Use `workspace/meta/memory.md` only for global stable knowledge. Do not read it
by default for every task.

Use `workspace/memory/INDEX.md` for topic routing before loading memory.

Write memory under one of these sections:

- `Preferences`
- `Project Facts`
- `Procedures`
- `Decisions`
- `Credential Hints`

Do not store:

- Secrets.
- Full task logs.
- One-off details.
- Unverified guesses.
- Long copied source text.

Before writing memory, deduplicate against existing lines and keep entries short.

## Active Context Rules

Update `workspace/meta/active-context.md` when:

- The user says to pause, stop, continue tomorrow, or save progress.
- A task produces a useful continuation anchor.
- Work remains partly complete.

Format:

```markdown
- **YYYY-MM-DD: topic (PAUSED|DONE|DECISION)** -> file path + one-sentence summary + continuation anchor
```

Keep the list short. Archive old entries later if this file grows beyond about 20 items.

## Friction Rules

Append to `workspace/meta/friction-log.md` when the same problem may repeat:

- unclear routing,
- missing config,
- wrong output format,
- repeated failed command,
- unclear permission boundary,
- missing or stale local context.

## Wiki Routing

Read `wiki/_schema.md` before writing to `wiki/`.

Use:

- `wiki/raw/` for raw material.
- `wiki/sources/` for one-source summaries.
- `wiki/entities/` for concrete objects.
- `wiki/concepts/` for reusable ideas.
- `wiki/explorations/` for cross-source judgments.

Write task deliverables to `output/` first. Ask before turning discussion or
research into durable wiki knowledge unless the user explicitly requested it.
