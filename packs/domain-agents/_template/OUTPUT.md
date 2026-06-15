# Domain Agent Output

## Directory

- [Default Format](#default-format)
- [Fields](#fields)

## Default Format

Use concise task-first output:

```text
Result:
Evidence:
Next:
```

## Fields

| Field | Required | Purpose |
|---|---|---|
| Result | yes | Direct answer or completed action |
| Evidence | when relevant | Local file, log, or command basis |
| Next | when useful | Concrete follow-up |
