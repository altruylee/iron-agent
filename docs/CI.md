# CI

## Directory

- [GitHub Actions](#github-actions)

## GitHub Actions

Minimal validation:

```yaml
name: iron-agent
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install -e .
      - run: iron check .
      - run: iron doctor .
```
