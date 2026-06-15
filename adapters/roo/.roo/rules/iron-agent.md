# Iron Agent Protocol

## Directory

- [Memory Routing](#memory-routing)
- [Rules](#rules)

## Memory Routing

Run this before memory reads:

```bash
python system/scripts/memory_router.py --task "<task>"
```

If paths are returned, read only those paths and apply their prompts/rules as an
overlay to the user's request. If no paths are returned, treat the request as
new content and continue normally. Use hot memory by default; warm/cold only
when routed.

## Rules

- `AGENTS.md` is canonical.
- Directory files contain routing only.
- Preserve low-token index limits.
- Do not store secrets.
- Ask before risky operations.
- Log useful prompt/rule/SOP candidates for nightly maintenance when practical.
