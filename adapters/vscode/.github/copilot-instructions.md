# Iron Agent Instructions for VS Code / GitHub Copilot

## Directory

- [Protocol](#protocol)
- [Memory Routing](#memory-routing)
- [Safety](#safety)

## Protocol

This repository uses Iron Agent. Follow `AGENTS.md` as the canonical workspace
contract. Iron Agent stores accumulated prompts, rules, SOPs, and preferences to
reduce tokens and personalize model behavior.

## Memory Routing

Do not read full memory folders. Route first:

```bash
python system/scripts/memory_router.py --task "<task>"
```

If paths are returned, read only those paths and apply their prompts/rules as an
overlay to the user's request. If no paths are returned, treat the request as
new content and continue normally.

Directory files are route-only and must stay low-token:

- top index <= 50 lines
- second-level index <= 100 lines
- third-level index <= 150 lines
- single SOP <= 200 lines

## Safety

- Do not store secrets.
- Ask before destructive changes.
- Preserve `## Directory` sections in Markdown.
- Keep responses concise and task-focused.
- Log useful prompt/rule/SOP candidates for nightly maintenance when practical.
