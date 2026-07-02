# Iron Agent for Claude Code

## Directory

- [Protocol](#protocol)
- [Memory](#memory)
- [Rules](#rules)

## Protocol

Use `AGENTS.md` as the canonical workspace contract.

For every task:

1. Before executing the user's task, identify all ambiguous or missing
   requirements, list the questions for user confirmation, and only produce the
   final result after everything necessary is clear.
2. Check `AGENTS.md` installation state.
3. Read `workspace/workspace-config.md`.
4. Read `workspace/meta/user-rules.md` if it exists.
5. For accumulated prompts/rules/SOPs, run `python system/scripts/memory_router.py --task "<task>" --semantic`.
6. If paths are returned, read only those paths and apply them as an overlay to
   the user's request.
7. If no paths are returned, treat the request as new content and continue normally.
8. Daily maintenance consolidates today's workspace traces through
   `system/skills/daily-conversation-consolidation.md`.
9. If the user types `iron capture`, summarize only currently visible context
   into `today-chat.md`, then run `iron capture` and send `/compact` as the
   final chat line.

## Memory

Do not scan all memory. Directory files are route-only and must stay low-token.
Iron Agent stores prompts, rules, SOPs, and preferences that make the model feel
more personalized while using fewer tokens.

Silent consolidation policy:

- Do not interrupt normal conversation for memory consolidation.
- During execution, leave only necessary structured traces in the workspace.
- Daily maintenance consolidates the day's workspace traces.
- Do not save full chat history; preserve only stable preferences, rules, SOPs,
  project facts, and unfinished context.
- `iron capture` in chat means capture currently visible context into
  `today-chat.md` first; it does not grant access to full platform transcripts.
- After reporting an `iron capture` result, send `/compact` as the final line.

Default command:

```bash
python system/scripts/memory_router.py --task "<task>" --semantic
```

## Rules

- Use Chinese by default.
- Ask before high-risk or external side-effect actions.
- Do not store secrets.
- Do not bypass P0-P3 permission tiers in `system/skills/codex-agent.md`.
- Do not save full chat history; daily maintenance consolidates only workspace traces.
- Nightly maintenance displays new candidates and potential conflicts; it does
  not wait for approval. The latest stable rule or candidate wins by default.
