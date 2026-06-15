# Domain Agent Rules

## Directory

- [Hard Rules](#hard-rules)
- [Permission Compatibility](#permission-compatibility)

## Hard Rules

- Preserve global P0 to P3 permission boundaries.
- Read the smallest relevant memory branch before broad scans.
- Do not invent domain facts; mark uncertain claims.
- Record reusable workflow friction in `workspace/meta/friction-log.md`.

## Permission Compatibility

Domain rules can be stricter than global rules, but cannot bypass approval requirements or write secrets.
