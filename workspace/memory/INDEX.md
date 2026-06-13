# Layered Memory Index

## Directory

- [Purpose](#purpose)
- [Layers](#layers)
- [Topic Routing](#topic-routing)
- [Rules](#rules)

## Purpose

This index routes memory reads by topic. Do not read all memory by default.

## Layers

| Layer | Path | Use |
|---|---|---|
| Short-Term Memory | `short-term/INDEX.md` | Minimal current-session cache |
| Episode Memory | `episodes/INDEX.md` | Topic and project fragments reached by tree paths |
| Semantic Memory | `semantic/INDEX.md` | Fixed SOPs and reusable rules |
| Shadow Review | `shadow-review/INDEX.md` | Async extraction queue and review outputs |

## Topic Routing

| Topic | Read path |
|---|---|
| 财务结算 | `episodes/finance/INDEX.md` -> matching fragment -> `semantic/sops/finance-settlement.md` if needed |
| 用户注册 | `episodes/user-registration/INDEX.md` -> matching fragment -> `semantic/sops/user-registration.md` if needed |
| 开发任务 | `packs/domain-agents/INDEX.md` -> matching domain runtime -> `episodes/development/INDEX.md` if needed |
| Unknown | Ask for the missing topic or create a narrow episode path after user confirmation |

## Rules

- Read only this index first, then the matched topic path.
- Do not load unrelated topic memory.
- If the input lacks the needed topic or project anchor, output `[缺少前置条件：请补充XX]` and stop.
- SOP extraction runs through shadow review or daily maintenance, not the live response path.
