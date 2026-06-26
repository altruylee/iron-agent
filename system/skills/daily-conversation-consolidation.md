# Daily Conversation Consolidation Skill

Use this skill during scheduled maintenance to organize the day's workspace
traces into concise memory candidates without interrupting normal conversations.

## Directory

- [Policy](#policy)
- [Sources](#sources)
- [Output](#output)
- [Limits](#limits)

## Policy

- 日常对话不打断用户。
- Codex 在执行任务时，只记录必要的结构化痕迹。
- 每天定时任务统一整理当天 workspace 痕迹。
- 不保存完整聊天记录，只沉淀稳定偏好、规则、SOP、项目事实和未完成上下文。
- Run only from daily maintenance or explicit user request.
- Do not ask the user questions during scheduled consolidation.
- Do not save full chat history.
- Do not store secrets, credentials, private keys, cookies, or raw sensitive data.
- Treat missing transcript access as normal: consolidate only files and logs
  available inside the workspace.
- Produce candidates for later review; do not force-merge durable memory during
  ordinary scheduled maintenance unless configured.

## Sources

Read only lightweight workspace traces:

- today's entries in `workspace/meta/task-log.jsonl`,
- `workspace/meta/active-context.md`,
- `workspace/meta/friction-log.md`,
- `workspace/meta/memory-candidates.md`,
- today's maintenance reports under `output/maintenance/`.

Platform chat transcripts are used only if the platform has already exported
them into the workspace. Iron Agent does not assume access to separate Codex,
Claude Code, or WorkBuddy conversations.

For user-initiated consolidation, run:

```bash
iron capture
```

By default, this reads `today-chat.md`, uses `YYYY-MM-DD daily chat` as the
title, extracts only stable preferences, rules, SOP candidates, project facts,
and unfinished context, and then runs daily maintenance with `--force`.

If the user types `iron capture` inside an agent chat, the agent must first
write `today-chat.md` from currently visible context only, without copying the
full transcript, and then run `iron capture`.

Advanced usage:

```bash
iron capture . --file chat.md --title "manual capture"
iron capture . --text "stable preference or rule"
iron capture . --file chat.md --no-maintenance
```

The command does not store the full chat text.
After successful capture, the source chat file is removed by default. Use
`--keep-source` only when raw input retention is intentional.

## Output

Write:

```text
output/maintenance/YYYY-MM-DD-conversation-digest.md
```

The digest should contain:

- tasks handled today,
- reusable prompt/rule/SOP candidates,
- repeated friction,
- continuation anchors,
- items that require user approval.

Daily maintenance then uses the digest plus task logs to update candidate files,
indexes, reports, and web output.

## Limits

- Keep each candidate one sentence.
- Prefer behavior rules and reusable procedures over narrative summaries.
- If no useful material exists, write an empty digest with a clear note.
