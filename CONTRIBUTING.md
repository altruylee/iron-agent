# Contributing

## Directory

- [Rules](#rules)
- [Checks](#checks)
- [Pull Requests](#pull-requests)

## Rules

- Keep every Markdown file with a `## Directory` section.
- Preserve low-token routing and tree indexes.
- Do not add personal paths, secrets, or machine-specific state.
- Keep field-specific workflows under `packs/domain-agents/`.

## Checks

Run:

```bash
python system/scripts/test_pack.py --root .
python system/scripts/release_check.py --root .
```

## Pull Requests

Explain the changed read path, files touched, and verification performed.
