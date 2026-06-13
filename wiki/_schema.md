# Personal Wiki Schema

## Directory

- [Core Rules](#core-rules)
- [Read Path From Here](#read-path-from-here)
- [Decision Tree](#decision-tree)
- [Naming](#naming)
- [Frontmatter Suggestions](#frontmatter-suggestions)

## Core Rules

1. Preserve raw material first.
2. Put single-source summaries in `wiki/sources/`.
3. Put people, companies, products, projects, and organizations in `wiki/entities/`.
4. Put reusable concepts and frameworks in `wiki/concepts/`.
5. Put cross-source judgments and tentative theses in `wiki/explorations/`.
6. Put task deliverables in `output/`.
7. Separate facts, inference, and unverified claims.

## Read Path From Here

| Need | Next location |
|---|---|
| Raw source archive | `wiki/raw/` |
| Single-source summary | `wiki/sources/` |
| Company/person/product/project | `wiki/entities/` |
| Reusable idea or framework | `wiki/concepts/` |
| Cross-source judgment | `wiki/explorations/` |
| Task output or draft | `output/` |

## Decision Tree

| Question | Yes | No |
|---|---|---|
| Is this raw material? | `wiki/raw/` | Continue |
| Is this a summary of one source? | `wiki/sources/` | Continue |
| Is this a concrete object? | `wiki/entities/` | Continue |
| Is this a reusable concept? | `wiki/concepts/` | Continue |
| Is this a cross-source judgment? | `wiki/explorations/` | `output/` or current task |

## Naming

| Type | Pattern |
|---|---|
| raw | `YYYY-MM-DD-{slug}.md` |
| source | `YYYY-MM-DD-{slug}.md` |
| entity | `{entity-name}.md` |
| concept | `{concept-slug}.md` |
| exploration | `YYYY-MM-DD-{topic}.md` |

## Frontmatter Suggestions

### Source Summary

```yaml
---
title:
date:
type: source-summary
source_path:
source_url:
raw_path:
status: processed
tags: []
---
```

### Exploration

```yaml
---
title:
date:
type: exploration
status: tentative
tags: []
---
```
