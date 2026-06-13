# Research Skill

Use this skill when the user asks to research, analyze, compare, or investigate
a topic using Iron Agent.

## Directory

- [Read Path From Here](#read-path-from-here)
- [Process](#process)
- [Output Shape](#output-shape)

## Read Path From Here

| Need | Next file or directory |
|---|---|
| Workspace rules | `workspace/workspace-config.md` |
| Execution and permission rules | `system/skills/codex-agent.md` |
| Wiki routing | `wiki/_schema.md` |
| Existing source summaries | `wiki/sources/` |
| Existing entities | `wiki/entities/` |
| Existing concepts | `wiki/concepts/` |
| Existing judgments | `wiki/explorations/` |
| Research outputs | `output/research/` |

## Process

1. Read `workspace/workspace-config.md`.
2. Read `wiki/_schema.md`.
3. Search local `wiki/` first.
4. Use web or data APIs only when local knowledge is insufficient or freshness matters.
5. Write a draft to `output/research/YYYY-MM-DD-{topic}.md`.
6. Label each factual claim as `[local]`, `[web]`, `[data]`, `[inference]`, or `[unverified]`.
7. Ask before writing long-term conclusions to `wiki/explorations/`.
8. Log the task and update active context.

## Output Shape

```markdown
# {Topic}

## Research Question

## Scope

## Core Conclusion

## Key Evidence

## Counter-evidence / Risks

## Key Data

## Open Questions

## Next Actions

Wiki check: {files checked and result}
```
