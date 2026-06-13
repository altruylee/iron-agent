# Memory Maintenance Skill

Use this skill to turn task-log memory candidates into durable, deduplicated
memory. This is Iron Agent's self-organizing memory loop.

## Directory

- [Read Path From Here](#read-path-from-here)
- [Layered Memory Model](#layered-memory-model)
- [Trigger](#trigger)
- [Process](#process)
- [SOP Promotion](#sop-promotion)
- [Review Rules](#review-rules)
- [Merge Rules](#merge-rules)
- [Verification](#verification)

## Read Path From Here

| Need | Next file |
|---|---|
| Layered memory index | `workspace/memory/INDEX.md` |
| Global durable memory | `workspace/meta/memory.md` |
| Source task logs | `workspace/meta/task-log.jsonl` |
| Execution rules | `system/skills/codex-agent.md` |
| Candidate script | `system/scripts/compact_memory.py` |
| Memory router | `system/scripts/memory_router.py` |
| Shadow reviewer | `system/scripts/shadow_reviewer.py` |
| Structure check | `system/scripts/structure_integrity.py` |
| Review output | `workspace/meta/memory-candidates.md` |

## Layered Memory Model

Memory is split into three layers:

- Short-Term Memory: `workspace/memory/short-term/`
- Episode Memory: `workspace/memory/episodes/`
- Semantic Memory: `workspace/memory/semantic/sops/`

Do not merge everything into `workspace/meta/memory.md`. Use
`workspace/memory/INDEX.md` to route by topic.

## Trigger

Run memory maintenance when:

- the user asks to organize, optimize, compact, clean, or update memory,
- `task-log.jsonl` has several new `memory_candidates`,
- a task creates a stable preference, project fact, procedure, decision, or credential hint,
- the daily scheduler or shadow reviewer runs.

Do not run memory maintenance during normal conversation unless the user asks.

## Process

1. Read `workspace/memory/INDEX.md`.
2. Read only the matched topic branch or async review queue.
3. Read recent `workspace/meta/task-log.jsonl` entries only as needed.
4. Run:

```bash
python system/scripts/compact_memory.py --root .
```

5. Review `workspace/meta/memory-candidates.md`.
6. Remove candidates that are transient, duplicated, speculative, too broad, or sensitive.
7. Promote stable SOPs to `workspace/memory/semantic/sops/`.
8. Shrink related short-term or review cache to links only.
9. Append a task log for the maintenance action.

Use `--apply` only when the candidate file is acceptable or the user explicitly asks for automatic merge:

```bash
python system/scripts/compact_memory.py --root . --apply
```

## SOP Promotion

Use shadow review for high-token SOP work:

```bash
python system/scripts/shadow_reviewer.py --root .
```

Rules:

- Copy good SOPs into the matching file under `workspace/memory/semantic/sops/`.
- Keep only concise executable steps.
- After promotion, clear or shrink the related cache file.
- Do not keep paying token cost to repeatedly merge historical conversation.

## Review Rules

Keep only durable items:

- `Preferences`: user communication or output preferences.
- `Project Facts`: stable paths, repo facts, enabled modules.
- `Procedures`: repeatable workflows.
- `Decisions`: long-lived permission or design decisions.
- `Credential Hints`: where secrets are configured, without secret values.

Reject:

- one-off task details,
- full command logs,
- guesses,
- raw copied source text,
- secrets or values that look like keys/tokens/passwords.

## Merge Rules

- Deduplicate against existing `memory.md`.
- Keep each line short.
- Preserve the existing section structure.
- Preserve the `## Directory` section and any upstream links.
- Preserve topic routing in `workspace/memory/INDEX.md`.
- Prefer revising an existing line over adding a near-duplicate.
- If unsure, leave the candidate in `memory-candidates.md` and ask the user.

## Verification

After maintenance:

1. Confirm `memory.md` still has the standard sections.
2. Confirm `workspace/memory/INDEX.md` routes the changed topic.
3. Confirm no obvious secrets were added.
4. Run `system/scripts/structure_integrity.py`.
5. Run `system/scripts/health_check.py`.
6. Log the maintenance task.
