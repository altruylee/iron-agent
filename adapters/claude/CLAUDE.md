# Iron Agent for Claude Code

## Directory

- [Protocol](#protocol)
- [Memory](#memory)
- [Rules](#rules)

## Protocol

Use `AGENTS.md` as the canonical workspace contract.

For every task:

1. Check `AGENTS.md` installation state.
2. Read `workspace/workspace-config.md`.
3. For accumulated prompts/rules/SOPs, run `python system/scripts/memory_router.py --task "<task>"`.
4. If paths are returned, read only those paths and apply them as an overlay to
   the user's request.
5. If no paths are returned, treat the request as new content and continue normally.
6. Record useful completed work and candidate prompts/rules in `workspace/meta/task-log.jsonl`.

## Memory

Do not scan all memory. Directory files are route-only and must stay low-token.
Iron Agent stores prompts, rules, SOPs, and preferences that make the model feel
more personalized while using fewer tokens.

Default command:

```bash
python system/scripts/memory_router.py --task "<task>"
```

## Rules

- Use Chinese by default.
- Ask before high-risk or external side-effect actions.
- Do not store secrets.
- Do not bypass P0-P3 permission tiers in `system/skills/codex-agent.md`.
- Nightly maintenance organizes new candidates and reports what changed.
