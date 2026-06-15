"""Small local Web UI for Iron Agent."""

from __future__ import annotations

import html
import json
import threading
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .core import (
    doctor_checks,
    evolution_candidates,
    read_config,
    read_move_log,
    read_task_entries,
    resolve_root,
    search_memory,
)


CSS = """
:root{color-scheme:light dark;--bg:#f7f8fa;--panel:#fff;--text:#17202a;--muted:#617083;--line:#d8dee8;--accent:#246bfe;--good:#168a53;--warn:#b86e00;--bad:#c92a2a}
@media (prefers-color-scheme:dark){:root{--bg:#101318;--panel:#171c23;--text:#e8edf5;--muted:#9aa7b8;--line:#2a3441;--accent:#7aa2ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 system-ui,Segoe UI,Arial,sans-serif}a{color:inherit;text-decoration:none}
.shell{display:grid;grid-template-columns:240px 1fr;min-height:100vh}.side{border-right:1px solid var(--line);padding:22px;background:var(--panel);position:sticky;top:0;height:100vh}.brand{font-weight:750;font-size:20px;margin-bottom:24px}.nav a{display:block;padding:9px 10px;border-radius:6px;color:var(--muted);margin:2px 0}.nav a:hover,.nav a.active{background:var(--bg);color:var(--text)}
.main{padding:28px;max-width:1280px}.top{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin-bottom:22px}.title h1{margin:0;font-size:26px}.title p{margin:4px 0 0;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:16px}.metric{font-size:28px;font-weight:760}.label{color:var(--muted);font-size:12px;text-transform:uppercase}.two{display:grid;grid-template-columns:1.2fr .8fr;gap:14px;margin-top:14px}
table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{font-size:12px;color:var(--muted);font-weight:650}.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 8px;color:var(--muted);font-size:12px}
pre{white-space:pre-wrap;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:12px;overflow:auto}.search{width:100%;padding:10px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--text)}.bar{height:8px;background:var(--bg);border-radius:99px;overflow:hidden}.bar span{display:block;height:100%;background:var(--accent)}
@media(max-width:860px){.shell{grid-template-columns:1fr}.side{height:auto;position:relative;border-right:0;border-bottom:1px solid var(--line)}.grid,.two{grid-template-columns:1fr}.main{padding:18px}}
"""


def esc(value: object) -> str:
    return html.escape(str(value))


def layout(root: Path, active: str, title: str, content: str) -> bytes:
    links = [
        ("Dashboard", "/"),
        ("Memory", "/memory"),
        ("Tasks", "/tasks"),
        ("Friction", "/friction"),
        ("Evolution", "/evolution"),
        ("Domain Agents", "/agents"),
        ("Settings", "/settings"),
    ]
    nav = "".join(f'<a class="{"active" if href == active else ""}" href="{href}">{label}</a>' for label, href in links)
    body = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} - Iron Agent</title><style>{CSS}</style></head>
<body><div class="shell"><aside class="side"><div class="brand">Iron Agent</div><nav class="nav">{nav}</nav></aside><main class="main">{content}</main></div></body></html>"""
    return body.encode("utf-8")


def page_header(title: str, subtitle: str) -> str:
    return f'<div class="top"><div class="title"><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div></div>'


def dashboard(root: Path) -> str:
    entries = read_task_entries(root)
    now = datetime.now(timezone.utc).astimezone()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    def parse_time(entry: dict) -> datetime | None:
        try:
            return datetime.fromisoformat(str(entry.get("time")))
        except ValueError:
            return None

    dates = [parse_time(entry) for entry in entries]
    today_count = sum(1 for item in dates if item and item.date() == today)
    week_count = sum(1 for item in dates if item and item.date() >= week_start)
    month_count = sum(1 for item in dates if item and item.date() >= month_start)
    friction = sum(len(entry.get("friction", [])) for entry in entries if not entry.get("invalid"))
    candidates = evolution_candidates(root)
    cards = [
        ("Today", today_count),
        ("This Week", week_count),
        ("This Month", month_count),
        ("Friction", friction),
    ]
    metrics = "".join(f'<div class="card"><div class="label">{label}</div><div class="metric">{value}</div></div>' for label, value in cards)
    cand_rows = "".join(f"<tr><td>{esc(c['type'])}</td><td>{esc(c['title'])}</td><td>{esc(c['hits'])}</td></tr>" for c in candidates)
    return page_header("Dashboard", str(root)) + f'<section class="grid">{metrics}</section><section class="two"><div class="card"><h2>Evolution Candidates</h2><table><tr><th>Type</th><th>Title</th><th>Hits</th></tr>{cand_rows}</table></div><div class="card"><h2>Token Saving</h2><div class="metric">45%</div><p class="label">Demo baseline from end-to-end sample</p><div class="bar"><span style="width:45%"></span></div></div></section>'


def memory(root: Path, query: str = "") -> str:
    memory_root = root / "workspace" / "memory"
    files = sorted(memory_root.rglob("*.md")) if memory_root.exists() else []
    rows = "".join(f"<tr><td>{esc(path.relative_to(root).as_posix())}</td><td><span class='pill'>md</span></td></tr>" for path in files[:300])
    results = search_memory(root, query) if query else []
    result_rows = "".join(f"<tr><td>{esc(item['path'])}</td><td>{esc(item['matches'])}</td></tr>" for item in results)
    return page_header("Memory Browser", "Tree view, search, and lightweight diff entry point.") + f"""<form><input class="search" name="q" value="{esc(query)}" placeholder="Search memory"></form><div class="two"><div class="card"><h2>Tree</h2><table>{rows}</table></div><div class="card"><h2>Search Results</h2><table><tr><th>Path</th><th>Matches</th></tr>{result_rows}</table><h2>Diff</h2><pre>Short-term vs semantic diff is available through file paths in this view.</pre></div></div>"""


def tasks(root: Path) -> str:
    entries = read_task_entries(root)[-1000:]
    rows = "".join(f"<tr><td>{esc(e.get('index'))}</td><td>{esc(e.get('time',''))}</td><td>{esc(e.get('task', e.get('raw','')))}</td><td>{esc(e.get('type','invalid'))}</td></tr>" for e in entries)
    return page_header("Task Log", "Recent task entries with timeline-style ordering.") + f'<div class="card"><table><tr><th>#</th><th>Time</th><th>Task</th><th>Type</th></tr>{rows}</table></div>'


def friction(root: Path) -> str:
    entries = read_task_entries(root)
    counts: dict[str, int] = {}
    for entry in entries:
        for item in entry.get("friction", []) if not entry.get("invalid") else []:
            counts[item] = counts.get(item, 0) + 1
    rows = "".join(f"<tr><td>{esc(k)}</td><td>{v}</td><td><div class='bar'><span style='width:{min(v * 20, 100)}%'></span></div></td></tr>" for k, v in sorted(counts.items(), key=lambda item: item[1], reverse=True))
    log = root / "workspace" / "meta" / "friction-log.md"
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else "No friction log yet."
    return page_header("Friction Log", "Friction frequency and source log.") + f'<div class="two"><div class="card"><table><tr><th>Type</th><th>Count</th><th>Heat</th></tr>{rows}</table></div><div class="card"><pre>{esc(text[:5000])}</pre></div></div>'


def evolution(root: Path) -> str:
    reports = sorted((root / "output" / "evolution").glob("*.md")) if (root / "output" / "evolution").exists() else []
    candidates = evolution_candidates(root)
    report_rows = "".join(f"<tr><td>{esc(path.name)}</td><td>{esc(path.relative_to(root).as_posix())}</td></tr>" for path in reports)
    cand_rows = "".join(f"<tr><td>{esc(c['type'])}</td><td>{esc(c['title'])}</td><td><span class='pill'>preview</span> <span class='pill'>apply</span> <span class='pill'>reject</span></td></tr>" for c in candidates)
    return page_header("Evolution", "Reports and candidate preview.") + f'<div class="two"><div class="card"><h2>Reports</h2><table>{report_rows}</table></div><div class="card"><h2>Candidates</h2><table>{cand_rows}</table></div></div>'


def agents(root: Path) -> str:
    agent_root = root / "packs" / "domain-agents"
    files = sorted(agent_root.rglob("*.md")) if agent_root.exists() else []
    rows = "".join(f"<tr><td>{esc(path.relative_to(root).as_posix())}</td><td><span class='pill'>enabled</span></td><td>0</td></tr>" for path in files[:300])
    return page_header("Domain Agents", "Installed domain agent files and enabled state.") + f'<div class="card"><table><tr><th>Agent</th><th>Status</th><th>Calls</th></tr>{rows}</table></div>'


def settings(root: Path) -> str:
    config = read_config(root)
    config_rows = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in config.items())
    moves = read_move_log(root)
    move_rows = "".join(f"<tr><td>{esc(m.get('time'))}</td><td>{esc(m.get('action'))}</td><td>{esc(m.get('status'))}</td></tr>" for m in moves[-50:])
    checks = doctor_checks(root)
    check_rows = "".join(f"<tr><td>{esc(c.name)}</td><td>{esc(c.status)}</td><td>{esc(c.message)}</td></tr>" for c in checks)
    return page_header("Settings", "Thresholds, backend placeholder, backup, and merge log.") + f'<div class="two"><div class="card"><h2>Evolution Thresholds</h2><table>{config_rows}</table><h2>Doctor</h2><table>{check_rows}</table></div><div class="card"><h2>Wiki / Memory Moves</h2><table>{move_rows}</table><h2>Backend</h2><pre>backend: codex\nadditional backends planned for v0.4.0</pre></div></div>'


class Handler(BaseHTTPRequestHandler):
    root: Path

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        path = parsed.path
        routes = {
            "/": lambda: dashboard(self.root),
            "/memory": lambda: memory(self.root, params.get("q", [""])[0]),
            "/tasks": lambda: tasks(self.root),
            "/friction": lambda: friction(self.root),
            "/evolution": lambda: evolution(self.root),
            "/agents": lambda: agents(self.root),
            "/settings": lambda: settings(self.root),
        }
        if path not in routes:
            self.send_error(404)
            return
        body = layout(self.root, path, path.strip("/") or "Dashboard", routes[path]())
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        return


def serve(root: str | Path, port: int = 8765, open_browser: bool = True) -> None:
    root_path = resolve_root(root)
    handler = type("IronAgentHandler", (Handler,), {"root": root_path})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}"
    if open_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    print(f"Iron Agent Web UI: {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping Iron Agent Web UI")
    finally:
        server.server_close()
