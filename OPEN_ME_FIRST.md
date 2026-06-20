# Open Me First

## Directory

- [What Happened](#what-happened)
- [Codex](#codex)
- [Claude Code](#claude-code)
- [WorkBuddy](#workbuddy)

## What Happened

Iron Agent has been copied into this folder, but setup is intentionally not
complete yet.

`AGENTS.md` keeps:

```text
install_status: 0
```

This is correct. The first AI session must collect your stable preferences,
paths, work types, permissions, and recurring tasks before changing the status
to `1`.

## Codex

Open this folder as the Codex workspace and say:

```text
初始化 Iron Agent
```

Codex should read `AGENTS.md`, see `install_status: 0`, run
`system/skills/initial-install.md`, ask the first-use questions, save your
answers, and only then mark installation complete.

If you installed Iron Agent from inside another Codex conversation, Codex cannot
silently switch the current thread to the newly created folder. Start a new
Codex thread with this folder selected, or install directly into the folder you
already opened.

## Claude Code

Open this folder in Claude Code. The included `CLAUDE.md` and `.claude/` files
tell Claude Code to use Iron Agent routing and maintenance.

## WorkBuddy

Open this folder in WorkBuddy. The included `WORKBUDDY.md` file tells WorkBuddy
to route memory internally. For invisible nightly maintenance, run once:

```bash
iron automation install . --tool all --apply
```
