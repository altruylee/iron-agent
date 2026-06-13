---
name: iron-agent-pack
description: Route Codex into a local Iron Agent workspace for low-token memory routing, task logs, permissions, domain agents, SOPs, daily maintenance, and workspace skills. Use when the user says to use Iron Agent, enter their AI workspace, continue prior work, save memory, install a workspace skill, organize research, or maintain their local Codex work system.
---

# Iron Agent Pack

## Directory

- [Workspace Path](#workspace-path)
- [Workflow](#workflow)
- [Triggers](#triggers)

## Workspace Path

Ask for the Iron Agent workspace path once unless the user already provided it.
The workspace root is the folder that contains `AGENTS.md`.

## Workflow

1. Open the workspace `AGENTS.md`.
2. Follow `Installation State`.
3. Use the task read path from `AGENTS.md`.
4. Route memory through `workspace/memory/INDEX.md`.
5. Do not scan the full workspace unless the indexed path is insufficient.
6. Log completed work according to the workspace protocol when practical.

## Triggers

Use this skill when the user says:

- "use iron-agent"
- "进入 iron-agent"
- "用我的工作包"
- "继续上次"
- "沉淀到 wiki"
- "整理记忆"
- "安装一个 skill"
- "维护我的 AI 工作区"
