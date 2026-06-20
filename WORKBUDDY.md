# Iron Agent for WorkBuddy

## Directory

- [Protocol](#protocol)
- [Memory](#memory)
- [Rules](#rules)

## Protocol

Use `AGENTS.md` as the canonical workspace contract.

For every task:

1. Check `AGENTS.md` installation state.
2. Read `workspace/workspace-config.md`.
3. Run `python system/scripts/memory_router.py --task "<task>" --json`.
4. If paths are returned, read only those files and apply them as prompt/rule/SOP overlay.
5. If no paths are returned, treat the request as new content and continue normally.
6. Record useful candidates for nightly maintenance when practical.

## Memory

Iron Agent stores accumulated prompts, rules, SOPs, and preferences. Do not scan
all memory folders. Route first, then read only returned leaf files.

## Rules

- Use Chinese by default.
- Keep responses concise and task-focused.
- Do not store secrets.
- Ask before destructive changes or external side effects.
- Nightly maintenance organizes new candidates and reports what changed.
