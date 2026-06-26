# Quickstart

## Directory

- [5 Minute Goal](#5-minute-goal)
- [Countdown](#countdown)
- [Steps](#steps)
- [Screenshots](#screenshots)
- [Stuck](#stuck)

## 5 Minute Goal

From zero to your first evolution report in 5 minutes.

## Countdown

| Time | Step | Expected result |
|---:|---|---|
| 0:00 | Install CLI | `iron --version` prints `0.4.1` |
| 1:00 | Initialize workspace | `install_status` becomes `1` |
| 2:00 | Run doctor | No `FAIL` checks |
| 3:00 | Generate report | Markdown report appears under `output/evolution/` |
| 4:00 | Inspect tasks and memory | CLI returns readable paths |
| 5:00 | Read demo | You can reproduce the end-to-end sample |

## Steps

1. Install the CLI from this repository.

```bash
python -m pip install -e .
iron --version
```

2. Create a fresh workspace.

```bash
iron init ../iron-agent-demo
```

3. Check the workspace.

```bash
iron doctor ../iron-agent-demo
iron check ../iron-agent-demo
```

4. Generate the first evolution report.

```bash
iron report ../iron-agent-demo
```

5. Inspect local state.

```bash
iron task list ../iron-agent-demo
iron memory route ../iron-agent-demo "开发一个测试修复流程"
```

6. Reproduce the full sample.

```bash
cd examples/end-to-end-demo
type README.md
```

Use `Get-Content README.md` instead of `type README.md` in PowerShell if your shell aliases differ.

## Screenshots

Add release screenshots at these paths before publishing:

- `docs/quickstart/01-install.png`
- `docs/quickstart/02-first-report.png`
- `docs/quickstart/03-doctor.png`

## Stuck

Run:

```bash
iron doctor . --fix
```

Then open `docs/TROUBLESHOOTING.md` and search by the exact error text.
