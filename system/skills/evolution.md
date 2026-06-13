# Evolution Skill

Use this skill when Iron Agent should improve itself from repeated use. The goal
is to turn repeated friction, repeated tasks, and recurring memory candidates
into better skills, templates, or domain agents.

## Directory

- [Read Path From Here](#read-path-from-here)
- [Signals](#signals)
- [Process](#process)
- [Outputs](#outputs)
- [Rules](#rules)

## Read Path From Here

| Need | Next file |
|---|---|
| Task history | `workspace/meta/task-log.jsonl` |
| Memory candidates | `workspace/meta/memory-candidates.md` |
| Friction | `workspace/meta/friction-log.md` |
| Installed skills | `system/skills/` |
| Domain agents | `packs/domain-agents/INDEX.md` |
| Evolution report script | `system/scripts/evolution_report.py` |
| Structure check | `system/scripts/structure_integrity.py` |

## Signals

Look for:

- repeated task names,
- repeated friction entries,
- repeated commands,
- repeated memory candidates,
- manual steps the user repeats,
- domain-specific work that does not belong in core skills.

## Process

1. Read recent `task-log.jsonl` and `friction-log.md`.
2. Identify repeated workflows.
3. Decide whether the improvement belongs in:
   - an existing core skill,
   - a new core skill,
   - a domain agent under `packs/domain-agents/`,
   - a template under `output/` or a domain pack.
4. Propose the change before editing if it changes behavior broadly.
5. Preserve directory sections and upstream links.
6. Run structure and health checks, then log the change.

## Outputs

Write improvement proposals to:

```text
output/evolution/
```

Generate an automatic report with:

```bash
python system/scripts/evolution_report.py --root .
```

Write user-specific domain workflows to:

```text
packs/domain-agents/
```

## Rules

- Do not create speculative abstractions.
- Prefer improving existing skills before adding new ones.
- Keep core generic; put field-specific agents in `packs/domain-agents/`.
- Run skill security audit before promoting installed or generated skills.
- Every evolved skill or memory change must keep `## Directory` and read paths current.
- If the current execution sandbox blocks Python writes to `output/`, record the
  limitation and still run `structure_integrity.py` and `health_check.py`.
