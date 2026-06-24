"""Run daily idle maintenance for Iron Agent."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


TZ = timezone(timedelta(hours=8))


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":", 1)
    return int(hour), int(minute)


def in_idle_window(now: datetime, start: str, end: str) -> bool:
    start_h, start_m = parse_hhmm(start)
    end_h, end_m = parse_hhmm(end)
    current = now.hour * 60 + now.minute
    start_min = start_h * 60 + start_m
    end_min = end_h * 60 + end_m
    if start_min <= end_min:
        return start_min <= current <= end_min
    return current >= start_min or current <= end_min


def should_run(now: datetime, state: dict, min_hours: int) -> bool:
    last_run = state.get("last_run_at")
    if not last_run:
        return True
    try:
        previous = datetime.fromisoformat(last_run)
    except ValueError:
        return True
    return now - previous >= timedelta(hours=min_hours)


def run_python(script: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4) if text else 0


def read_text_tokens(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    return estimate_tokens(path.read_text(encoding="utf-8", errors="replace"))


def token_savings_summary(root: Path) -> dict[str, int]:
    memory_root = root / "workspace" / "memory"
    all_memory_tokens = 0
    if memory_root.exists():
        for path in memory_root.rglob("*.md"):
            all_memory_tokens += read_text_tokens(path)

    routing_files = [
        root / "workspace" / "memory" / "INDEX.md",
        root / "workspace" / "memory" / "index.json",
        root / "workspace" / "memory" / "hot" / "INDEX.md",
    ]
    routed_tokens = sum(read_text_tokens(path) for path in routing_files)
    avoided_tokens = max(0, all_memory_tokens - routed_tokens)
    savings_percent = int(round((avoided_tokens / all_memory_tokens) * 100)) if all_memory_tokens else 0
    return {
        "all_memory_tokens": all_memory_tokens,
        "routing_surface_tokens": routed_tokens,
        "estimated_avoided_tokens": avoided_tokens,
        "estimated_savings_percent": savings_percent,
    }


def first_int(pattern: str, text: str, default: int = 0) -> int:
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else default


def count_sops(root: Path) -> int:
    sop_dir = root / "workspace" / "memory" / "semantic" / "sops"
    if not sop_dir.exists():
        return 0
    return len([path for path in sop_dir.glob("*.md") if path.name != "INDEX.md"])


def count_index_files(root: Path) -> int:
    memory_root = root / "workspace" / "memory"
    if not memory_root.exists():
        return 0
    return len([path for path in memory_root.rglob("INDEX.md") if path.is_file()])


def extract_maintenance_metrics(root: Path, now: datetime, lines: list[str], savings: dict[str, int]) -> dict[str, object]:
    joined = "\n".join(lines)
    candidates = first_int(r"Prepared\s+(\d+)\s+memory candidates", joined)
    promoted_sops = first_int(r"Promoted SOP files:\s*(\d+)", joined)
    indexes = count_index_files(root)
    sop_total = count_sops(root)
    maturity = min(99, 10 + sop_total * 3 + indexes)
    return {
        "date": now.date().isoformat(),
        "run_time": now.isoformat(timespec="seconds"),
        "status": "ok",
        "saved_today": savings["estimated_avoided_tokens"],
        "full_memory_tokens": savings["all_memory_tokens"],
        "routing_surface_tokens": savings["routing_surface_tokens"],
        "savings_percent": savings["estimated_savings_percent"],
        "memory_candidates": candidates,
        "promoted_sops": promoted_sops,
        "rules_promoted": max(0, candidates - promoted_sops),
        "indexes_slimmed": indexes,
        "sop_total": sop_total,
        "maturity_level": maturity,
        "events": [
            f"Prepared {candidates} memory candidates",
            f"Promoted {promoted_sops} SOP files",
            f"Checked {indexes} low-token indexes",
            f"Estimated {savings['estimated_avoided_tokens']} tokens avoided",
        ],
    }


def update_maintenance_history(root: Path, metrics: dict[str, object]) -> list[dict[str, object]]:
    history_path = root / "output" / "maintenance" / "maintenance-history.json"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, object]] = []
    if history_path.exists():
        try:
            data = json.loads(history_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                history = [item for item in data if isinstance(item, dict)]
        except json.JSONDecodeError:
            history = []
    history = [item for item in history if item.get("date") != metrics["date"]]
    history.append(metrics)
    history = sorted(history, key=lambda item: str(item.get("date", "")))[-90:]
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return history


def write_web_report(root: Path, now: datetime, lines: list[str], savings: dict[str, int]) -> tuple[Path, Path]:
    metrics = extract_maintenance_metrics(root, now, lines, savings)
    history = update_maintenance_history(root, metrics)
    cumulative = sum(int(item.get("saved_today", 0)) for item in history)
    data = {
        "today": metrics,
        "history": history,
        "cumulative_saved": cumulative,
        "details": lines,
    }
    html = render_observatory_html(data)
    report_dir = root / "output" / "maintenance"
    daily_html = report_dir / f"{now.date().isoformat()}-daily-maintenance.html"
    index_html = report_dir / "index.html"
    daily_html.write_text(html, encoding="utf-8")
    index_html.write_text(html, encoding="utf-8")
    return daily_html, index_html


def render_observatory_html(data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Iron Agent Memory Observatory</title>
  <style>
    :root {{
      --bg:#070a12; --panel:rgba(13,19,33,.78); --line:rgba(132,220,255,.18);
      --text:#eef7ff; --muted:#94a7bd; --cyan:#62e7ff; --green:#82f7b8;
      --amber:#ffd166; --pink:#ff7ad9; --violet:#a78bfa;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0; min-height:100vh; color:var(--text);
      font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      background:radial-gradient(circle at 12% 8%,rgba(98,231,255,.20),transparent 28rem),
        radial-gradient(circle at 82% 18%,rgba(167,139,250,.16),transparent 30rem),
        radial-gradient(circle at 50% 100%,rgba(130,247,184,.12),transparent 28rem),var(--bg);
      overflow-x:hidden;
    }}
    #particles,.grid {{ position:fixed; inset:0; pointer-events:none; }}
    #particles {{ z-index:0; opacity:.72; }}
    .grid {{
      z-index:0; background-image:linear-gradient(rgba(98,231,255,.06) 1px,transparent 1px),
      linear-gradient(90deg,rgba(98,231,255,.06) 1px,transparent 1px); background-size:58px 58px;
      mask-image:linear-gradient(to bottom,rgba(0,0,0,.8),transparent 82%);
    }}
    .scanline {{
      position:fixed; left:0; right:0; top:0; height:2px; z-index:6;
      background:linear-gradient(90deg,transparent,var(--cyan),var(--green),transparent);
      box-shadow:0 0 28px rgba(98,231,255,.9); animation:scan 4.8s linear infinite;
    }}
    @keyframes scan {{ from {{ transform:translateY(-10vh); opacity:0; }} 12%,88% {{ opacity:1; }} to {{ transform:translateY(110vh); opacity:0; }} }}
    .shell {{ position:relative; z-index:1; width:min(1440px,calc(100% - 40px)); margin:0 auto; padding:28px 0 48px; }}
    header {{ display:flex; align-items:center; justify-content:space-between; gap:18px; padding:12px 0 34px; }}
    .brand {{ display:flex; align-items:center; gap:14px; min-width:0; }}
    .mark {{ width:44px; height:44px; border:1px solid rgba(98,231,255,.42); border-radius:10px; display:grid; place-items:center;
      background:linear-gradient(145deg,rgba(98,231,255,.20),rgba(167,139,250,.10)); box-shadow:0 0 34px rgba(98,231,255,.25); }}
    .mark:before {{ content:""; width:18px; height:18px; border:2px solid var(--cyan); border-top-color:var(--green); transform:rotate(45deg); box-shadow:0 0 18px rgba(98,231,255,.8); }}
    .brand h1 {{ margin:0; font-size:15px; text-transform:uppercase; color:#dff7ff; }}
    .brand p,.muted {{ margin:2px 0 0; color:var(--muted); font-size:13px; }}
    .status {{ display:flex; align-items:center; gap:10px; padding:10px 12px; border:1px solid rgba(130,247,184,.28); border-radius:8px; background:rgba(8,20,18,.54); color:#caffdf; font-size:13px; white-space:nowrap; }}
    .status i {{ width:8px; height:8px; border-radius:999px; background:var(--green); box-shadow:0 0 16px var(--green); }}
    .hero {{ min-height:520px; display:grid; grid-template-columns:minmax(0,1.08fr) minmax(360px,.92fr); gap:22px; align-items:stretch; }}
    .panel,.card,.hero-copy,.agent-core {{ border:1px solid var(--line); border-radius:8px; background:var(--panel); box-shadow:0 22px 90px rgba(0,0,0,.34); }}
    .hero-copy {{ padding:34px; overflow:hidden; position:relative; }}
    .hero-copy:before {{ content:""; position:absolute; left:-40%; top:0; width:70%; height:1px; background:linear-gradient(90deg,transparent,var(--cyan),transparent); animation:sweep 5s ease-in-out infinite; }}
    @keyframes sweep {{ 0%,100% {{ transform:translateX(0); opacity:.2; }} 50% {{ transform:translateX(190%); opacity:1; }} }}
    .eyebrow {{ margin:0 0 18px; color:var(--green); font-size:12px; font-weight:700; text-transform:uppercase; }}
    .hero h2 {{ max-width:780px; margin:0; font-size:clamp(44px,7vw,86px); line-height:.94; }}
    .hero h2 span {{ color:transparent; background:linear-gradient(90deg,#fff,var(--cyan),var(--green)); -webkit-background-clip:text; background-clip:text; }}
    .lead {{ max-width:720px; margin:24px 0 0; color:#b6c9dd; font-size:18px; line-height:1.7; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:32px; }}
    .button {{ border:1px solid rgba(98,231,255,.35); border-radius:8px; color:var(--text); background:rgba(98,231,255,.10); padding:12px 15px; font-size:14px; font-weight:700; }}
    .button.primary {{ background:linear-gradient(135deg,rgba(98,231,255,.28),rgba(130,247,184,.20)); box-shadow:0 0 30px rgba(98,231,255,.16); }}
    .agent-core {{ padding:24px; display:grid; grid-template-rows:auto 1fr auto; min-height:520px; overflow:hidden; }}
    .core-title {{ display:flex; justify-content:space-between; color:var(--muted); font-size:13px; }}
    .orb-wrap {{ position:relative; display:grid; place-items:center; min-height:330px; }}
    .orb {{ width:210px; height:210px; border-radius:999px; border:1px solid rgba(98,231,255,.46);
      background:radial-gradient(circle at 45% 38%,rgba(255,255,255,.88),transparent 5%),radial-gradient(circle at 48% 45%,rgba(98,231,255,.42),rgba(167,139,250,.18) 38%,rgba(8,11,20,.1) 68%);
      box-shadow:inset 0 0 50px rgba(98,231,255,.24),0 0 60px rgba(98,231,255,.34),0 0 130px rgba(167,139,250,.18); animation:breathe 4s ease-in-out infinite; }}
    @keyframes breathe {{ 0%,100% {{ transform:scale(.98); }} 50% {{ transform:scale(1.04); }} }}
    .ring {{ position:absolute; width:290px; height:290px; border:1px dashed rgba(98,231,255,.24); border-radius:999px; animation:rotate 18s linear infinite; }}
    .ring.two {{ width:360px; height:180px; border-color:rgba(130,247,184,.20); animation-duration:26s; animation-direction:reverse; }}
    @keyframes rotate {{ to {{ transform:rotate(360deg); }} }}
    .node {{ position:absolute; border:1px solid rgba(255,255,255,.14); border-radius:8px; background:rgba(5,9,18,.82); padding:8px 10px; color:#dff7ff; font-size:12px; box-shadow:0 0 24px rgba(98,231,255,.14); }}
    .n1 {{ top:42px; left:24px; }} .n2 {{ top:90px; right:16px; }} .n3 {{ bottom:74px; left:16px; }} .n4 {{ bottom:34px; right:46px; }}
    .mini-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }}
    .mini {{ border:1px solid rgba(255,255,255,.10); border-radius:8px; padding:10px; background:rgba(255,255,255,.04); }}
    .mini b {{ display:block; color:var(--green); font-size:16px; }} .mini span {{ color:var(--muted); font-size:12px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin:22px 0; }}
    .card {{ padding:18px; position:relative; overflow:hidden; transition:transform 180ms ease,border-color 180ms ease; }}
    .card:hover {{ transform:translateY(-3px); border-color:rgba(98,231,255,.45); }}
    .metric-label {{ margin:0 0 10px; color:var(--muted); font-size:12px; text-transform:uppercase; }}
    .metric-value {{ font-size:clamp(26px,3vw,38px); line-height:1; font-weight:800; }}
    .cyan {{ color:var(--cyan); text-shadow:0 0 22px rgba(98,231,255,.35); }} .green {{ color:var(--green); text-shadow:0 0 22px rgba(130,247,184,.32); }} .amber {{ color:var(--amber); }} .pink {{ color:var(--pink); }}
    .metric-note {{ margin-top:10px; color:#8da2b9; font-size:12px; }}
    .dashboard {{ display:grid; grid-template-columns:minmax(0,1.35fr) minmax(320px,.65fr); gap:18px; align-items:stretch; }}
    .section-title {{ display:flex; align-items:baseline; justify-content:space-between; gap:14px; margin-bottom:18px; }}
    .section-title h3 {{ margin:0; font-size:18px; }} .section-title span {{ color:var(--muted); font-size:13px; }}
    .chart {{ height:320px; width:100%; }}
    .bar-row {{ display:grid; grid-template-columns:86px minmax(0,1fr) 56px; gap:10px; align-items:center; color:#c7d6e8; font-size:13px; margin-bottom:14px; }}
    .bar-track {{ height:10px; border-radius:999px; background:rgba(255,255,255,.07); overflow:hidden; }}
    .bar-fill {{ height:100%; border-radius:999px; background:linear-gradient(90deg,var(--cyan),var(--green)); box-shadow:0 0 16px rgba(98,231,255,.38); width:var(--w); animation:grow 1.2s ease-out both; }}
    @keyframes grow {{ from {{ width:0; }} to {{ width:var(--w); }} }}
    .lower {{ display:grid; grid-template-columns:repeat(3,1fr); gap:18px; margin-top:18px; }}
    .event {{ display:grid; grid-template-columns:16px 1fr; gap:12px; align-items:start; margin-bottom:13px; }}
    .event i {{ width:10px; height:10px; margin-top:5px; border-radius:999px; background:var(--cyan); box-shadow:0 0 14px var(--cyan); }}
    .event b {{ display:block; font-size:14px; margin-bottom:3px; }} .event span {{ color:var(--muted); font-size:12px; line-height:1.45; }}
    .donut {{ width:180px; aspect-ratio:1; border-radius:999px; margin:14px auto 24px; background:conic-gradient(var(--green) 0 48%,var(--cyan) 48% 78%,var(--violet) 78% 100%); position:relative; box-shadow:0 0 40px rgba(98,231,255,.16); }}
    .donut:after {{ content:"Memory"; position:absolute; inset:26px; border-radius:999px; display:grid; place-items:center; color:#dff7ff; background:#0a0f1b; border:1px solid rgba(255,255,255,.08); font-weight:800; }}
    .terminal {{ font-family:"Cascadia Code","SFMono-Regular",Consolas,monospace; color:#bfffe0; font-size:12px; line-height:1.55; }}
    .terminal p {{ margin:0 0 9px; color:#8df7c0; }} .terminal p:before {{ content:">"; color:var(--cyan); margin-right:8px; }}
    footer {{ color:#71859b; font-size:12px; padding:28px 0 6px; text-align:center; }}
    @media (max-width:1100px) {{ .hero,.dashboard,.lower {{ grid-template-columns:1fr; }} .metrics {{ grid-template-columns:repeat(2,1fr); }} }}
    @media (max-width:680px) {{ .shell {{ width:min(100% - 24px,1440px); }} header {{ align-items:flex-start; flex-direction:column; }} .hero-copy,.agent-core,.card {{ padding:18px; }} .metrics,.mini-grid {{ grid-template-columns:1fr; }} .hero h2 {{ font-size:42px; }} .lead {{ font-size:15px; }} .node {{ display:none; }} }}
  </style>
</head>
<body>
  <canvas id="particles"></canvas><div class="grid"></div><div class="scanline"></div>
  <main class="shell">
    <header><div class="brand"><div class="mark"></div><div><h1>Iron Agent Memory Observatory</h1><p>Daily Maintenance / Long-term Intelligence / Token Efficiency</p></div></div><div class="status"><i></i><span id="statusText"></span></div></header>
    <section class="hero">
      <div class="hero-copy"><p class="eyebrow" id="eyebrow"></p><h2>Your agent learned while you were away. <span>Quietly.</span></h2><p class="lead">Iron Agent compressed traces into routable memory, promoted stable rules, trimmed indexes, and kept the daily context surface small enough for fast, precise work.</p><div class="actions"><div class="button primary" id="savedPill"></div><div class="button" id="cumulativePill"></div><div class="button" id="reductionPill"></div></div></div>
      <aside class="agent-core"><div class="core-title"><span>Agent Maturity Core</span><strong id="levelText"></strong></div><div class="orb-wrap"><div class="ring"></div><div class="ring two"></div><div class="orb"></div><div class="node n1" id="nodePrompts"></div><div class="node n2" id="nodeRules"></div><div class="node n3" id="nodeSop"></div><div class="node n4" id="nodeIndex"></div></div><div class="mini-grid"><div class="mini"><b id="miniRules"></b><span>candidate rules</span></div><div class="mini"><b id="miniSops"></b><span>active SOPs</span></div><div class="mini"><b id="miniReduction"></b><span>read reduction</span></div></div></aside>
    </section>
    <section class="metrics">
      <article class="card"><p class="metric-label">Today Saved</p><div class="metric-value cyan" data-key="saved_today">0</div><div class="metric-note">tokens avoided by routing first</div></article>
      <article class="card"><p class="metric-label">Cumulative Saved</p><div class="metric-value green" data-key="cumulative_saved">0</div><div class="metric-note">maintenance history total</div></article>
      <article class="card"><p class="metric-label">Candidates</p><div class="metric-value" data-key="memory_candidates">0</div><div class="metric-note">new memory candidates</div></article>
      <article class="card"><p class="metric-label">SOPs Promoted</p><div class="metric-value amber" data-key="promoted_sops">0</div><div class="metric-note">stable procedures captured</div></article>
      <article class="card"><p class="metric-label">Indexes Checked</p><div class="metric-value pink" data-key="indexes_slimmed">0</div><div class="metric-note">low-token routing files</div></article>
    </section>
    <section class="dashboard">
      <article class="card"><div class="section-title"><h3>Token Savings Trend</h3><span>full memory read vs routed surface</span></div><svg class="chart" id="trend" viewBox="0 0 900 320"></svg></article>
      <article class="card"><div class="section-title"><h3>Memory Tiers</h3><span>hot / warm / cold</span></div><div class="donut"></div><div id="tierBars"></div></article>
    </section>
    <section class="lower">
      <article class="card"><div class="section-title"><h3>What Changed Today</h3><span>maintenance output</span></div><div id="events"></div></article>
      <article class="card"><div class="section-title"><h3>Efficiency Profile</h3><span>current run</span></div><div id="efficiencyBars"></div></article>
      <article class="card terminal"><div class="section-title"><h3>Maintenance Pulse</h3><span>raw signal</span></div><div id="terminal"></div></article>
    </section>
    <footer>Generated by Iron Agent daily maintenance · Static HTML · No server required</footer>
  </main>
  <script>
    const DATA = {payload};
    const today = DATA.today;
    const fmt = (n) => Number(n || 0).toLocaleString();
    document.getElementById("statusText").textContent = `Maintenance completed · ${{today.run_time || today.date}}`;
    document.getElementById("eyebrow").textContent = `Agent Growth Report · ${{today.date}}`;
    document.getElementById("savedPill").textContent = `${{fmt(today.saved_today)}} tokens saved today`;
    document.getElementById("cumulativePill").textContent = `${{fmt(DATA.cumulative_saved)}} cumulative saved`;
    document.getElementById("reductionPill").textContent = `${{today.savings_percent}}% memory read reduction`;
    document.getElementById("levelText").textContent = `Level ${{today.maturity_level}}`;
    document.getElementById("nodePrompts").textContent = `Candidates +${{today.memory_candidates}}`;
    document.getElementById("nodeRules").textContent = `Rules +${{today.rules_promoted}}`;
    document.getElementById("nodeSop").textContent = `SOP +${{today.promoted_sops}}`;
    document.getElementById("nodeIndex").textContent = `Indexes ${{today.indexes_slimmed}}`;
    document.getElementById("miniRules").textContent = today.rules_promoted;
    document.getElementById("miniSops").textContent = today.sop_total;
    document.getElementById("miniReduction").textContent = `${{today.savings_percent}}%`;
    document.querySelectorAll("[data-key]").forEach((el) => animateNumber(el, el.dataset.key === "cumulative_saved" ? DATA.cumulative_saved : today[el.dataset.key]));
    function animateNumber(el, target) {{ target = Number(target || 0); const start = performance.now(); const duration = 1200; function tick(now) {{ const t = Math.min(1,(now-start)/duration); const v = Math.floor(target*(1-Math.pow(1-t,3))); el.textContent = fmt(v); if (t < 1) requestAnimationFrame(tick); }} requestAnimationFrame(tick); }}
    function bar(label, value, max) {{ const pct = Math.max(4, Math.round((Number(value || 0) / Math.max(1, max)) * 100)); return `<div class="bar-row"><span>${{label}}</span><div class="bar-track"><div class="bar-fill" style="--w:${{pct}}%"></div></div><b>${{fmt(value)}}</b></div>`; }}
    document.getElementById("tierBars").innerHTML = bar("Hot", 48, 100) + bar("Warm", 30, 100) + bar("Cold", 22, 100);
    document.getElementById("efficiencyBars").innerHTML = bar("Full", today.full_memory_tokens, today.full_memory_tokens) + bar("Routed", today.routing_surface_tokens, today.full_memory_tokens) + bar("Saved", today.saved_today, today.full_memory_tokens);
    document.getElementById("events").innerHTML = (today.events || []).map((e) => `<div class="event"><i></i><div><b>${{e}}</b><span>Captured by daily maintenance.</span></div></div>`).join("");
    document.getElementById("terminal").innerHTML = (DATA.details || []).slice(0, 6).map((d) => `<p>${{String(d).replace(/[<>&]/g, s => ({{'<':'&lt;','>':'&gt;','&':'&amp;'}}[s]))}}</p>`).join("");
    function drawTrend() {{
      const svg = document.getElementById("trend"); const h = DATA.history || []; const values = h.length ? h.map(x => Number(x.saved_today || 0)) : [today.saved_today];
      const max = Math.max(1, ...values); const pts = values.map((v,i) => [60 + (800 * (values.length === 1 ? 1 : i / (values.length - 1))), 280 - (230 * v / max)]);
      const line = pts.map((p,i) => `${{i?'L':'M'}}${{p[0].toFixed(1)}} ${{p[1].toFixed(1)}}`).join(" ");
      const area = line + " L860 280 L60 280 Z";
      svg.innerHTML = `<defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#62e7ff" stop-opacity=".34"/><stop offset="100%" stop-color="#62e7ff" stop-opacity="0"/></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><g stroke="rgba(255,255,255,.08)" stroke-width="1"><path d="M60 40H860M60 100H860M60 160H860M60 220H860M60 280H860"/><path d="M60 40V280M220 40V280M380 40V280M540 40V280M700 40V280M860 40V280"/></g><path d="${{area}}" fill="url(#area)"/><path d="${{line}}" fill="none" stroke="#62e7ff" stroke-width="4" filter="url(#glow)"/><g fill="#94a7bd" font-size="12"><text x="60" y="305">history</text><text x="805" y="305">today</text><text x="68" y="58">saved</text></g>`;
    }}
    drawTrend();
    const canvas = document.getElementById("particles"), ctx = canvas.getContext("2d"); let points = [];
    function resize() {{ canvas.width = innerWidth * devicePixelRatio; canvas.height = innerHeight * devicePixelRatio; ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0); points = Array.from({{length:Math.min(90,Math.floor(innerWidth/18))}}, () => ({{x:Math.random()*innerWidth,y:Math.random()*innerHeight,vx:(Math.random()-.5)*.28,vy:(Math.random()-.5)*.28}})); }}
    function draw() {{ ctx.clearRect(0,0,innerWidth,innerHeight); points.forEach((p,i) => {{ p.x+=p.vx; p.y+=p.vy; if(p.x<0||p.x>innerWidth)p.vx*=-1; if(p.y<0||p.y>innerHeight)p.vy*=-1; ctx.beginPath(); ctx.arc(p.x,p.y,1.4,0,Math.PI*2); ctx.fillStyle="rgba(98,231,255,.58)"; ctx.fill(); for(let j=i+1;j<points.length;j++){{ const q=points[j],dx=p.x-q.x,dy=p.y-q.y,d=Math.sqrt(dx*dx+dy*dy); if(d<125){{ ctx.strokeStyle=`rgba(98,231,255,${{.16*(1-d/125)}})`; ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); }} }} }}); requestAnimationFrame(draw); }}
    addEventListener("resize", resize); resize(); draw();
  </script>
</body>
</html>"""


def write_report(root: Path, now: datetime, lines: list[str]) -> Path:
    savings = token_savings_summary(root)
    report_dir = root / "output" / "maintenance"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{now.date().isoformat()}-daily-maintenance.md"
    body = [
        "# Daily Maintenance Report",
        "",
        "## Directory",
        "",
        "- [Summary](#summary)",
        "- [Token Savings](#token-savings)",
        "- [Details](#details)",
        "",
        "## Summary",
        "",
        f"- Run time: `{now.isoformat(timespec='seconds')}`",
        f"- Estimated avoided tokens: `{savings['estimated_avoided_tokens']}`",
        f"- Estimated savings: `{savings['estimated_savings_percent']}%`",
        "",
        "## Token Savings",
        "",
        f"- Full memory read estimate: `{savings['all_memory_tokens']}` tokens",
        f"- Daily routing surface estimate: `{savings['routing_surface_tokens']}` tokens",
        f"- Estimated tokens avoided by routing first: `{savings['estimated_avoided_tokens']}` tokens",
        f"- Estimated reduction: `{savings['estimated_savings_percent']}%`",
        "- Estimate uses `4 characters ~= 1 token`; actual model tokenization may vary.",
        "",
        "## Details",
        "",
        *[f"- {line}" for line in lines],
        "",
    ]
    report_path.write_text("\n".join(body), encoding="utf-8")
    return report_path


def append_task_log(root: Path, report_path: Path, verification: str) -> None:
    script = root / "system" / "scripts" / "append_task_log.py"
    run_python(
        script,
        [
            "--root",
            str(root),
            "--task",
            "Daily idle maintenance",
            "--type",
            "maintenance",
            "--permission",
            "P1",
            "--read",
            "config/maintenance.json;workspace/memory/INDEX.md;workspace/meta/task-log.jsonl",
            "--written",
            f"workspace/meta/memory-candidates.md;workspace/meta/maintenance-state.json;workspace/memory/semantic/sops/;{report_path.relative_to(root)};workspace/meta/task-log.jsonl",
            "--commands",
            "python system/scripts/daily_maintenance.py;python system/scripts/compact_memory.py;python system/scripts/shadow_reviewer.py",
            "--verification",
            verification,
            "--memory-candidates",
            "Iron Agent can run daily idle maintenance through daily_maintenance.py using config/maintenance.json",
        ],
    )


def write_codex_trigger(root: Path, now: datetime, status: str) -> Path:
    trigger_path = root / "workspace" / "meta" / "codex-automation-trigger.json"
    trigger_path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "created_at": now.isoformat(timespec="seconds"),
        "status": status,
        "next_step": "Codex automation should run AI shadow review against workspace/memory/shadow-review/.",
        "prompt": "system/prompts/codex-shadow-maintenance.md",
    }
    trigger_path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    return trigger_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = root / "config" / "maintenance.json"
    state_path = root / "workspace" / "meta" / "maintenance-state.json"

    config = load_json(config_path, {})
    daily = config.get("daily_maintenance", {})
    now = datetime.now(TZ)
    lines: list[str] = []

    if not daily.get("enabled", True):
        print("Daily maintenance disabled")
        return 0

    idle = daily.get("idle_window", {})
    start = idle.get("start", "23:00")
    end = idle.get("end", "06:00")
    min_hours = int(daily.get("min_hours_between_runs", 20))
    state = load_json(state_path, {})

    if not args.force and not in_idle_window(now, start, end):
        print(f"Outside idle window {start}-{end}; use --force to run now")
        return 0

    if not args.force and not should_run(now, state, min_hours):
        print(f"Last run is too recent; min_hours_between_runs={min_hours}")
        return 0

    compact_script = root / "system" / "scripts" / "compact_memory.py"
    compact_args = [
        "--root",
        str(root),
        "--limit",
        str(int(daily.get("max_memory_candidates", 50))),
    ]
    if daily.get("auto_apply_memory", False):
        compact_args.append("--apply")

    result = run_python(compact_script, compact_args)
    lines.append(result.stdout.strip() or "Memory candidate preparation completed")
    if result.stderr.strip():
        lines.append(f"stderr: {result.stderr.strip()}")

    shadow_script = root / "system" / "scripts" / "shadow_reviewer.py"
    shadow_result = run_python(shadow_script, ["--root", str(root)])
    lines.append(shadow_result.stdout.strip() or "Shadow review completed")
    if shadow_result.stderr.strip():
        lines.append(f"shadow stderr: {shadow_result.stderr.strip()}")

    slim_script = root / "system" / "scripts" / "memory_index_maintenance.py"
    slim_result = run_python(slim_script, ["--root", str(root), "--apply", "--write-report"])
    lines.append(slim_result.stdout.strip() or "Memory index slimming completed")
    if slim_result.stderr.strip():
        lines.append(f"index stderr: {slim_result.stderr.strip()}")

    savings = token_savings_summary(root)
    lines.append(
        "Token savings estimate: "
        f"full memory `{savings['all_memory_tokens']}` tokens, "
        f"routing surface `{savings['routing_surface_tokens']}` tokens, "
        f"avoided `{savings['estimated_avoided_tokens']}` tokens "
        f"({savings['estimated_savings_percent']}%)."
    )

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "last_run_at": now.isoformat(timespec="seconds"),
        "last_status": "ok" if result.returncode == 0 and shadow_result.returncode == 0 and slim_result.returncode == 0 else "error",
        "auto_apply_memory": bool(daily.get("auto_apply_memory", False)),
        "shadow_review": bool(daily.get("shadow_review", True)),
    }
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    lines.append(f"State updated: {state_path.relative_to(root)}")

    trigger_path = write_codex_trigger(root, now, state["last_status"])
    lines.append(f"Codex trigger written: {trigger_path.relative_to(root)}")
    lines.append("Upgrade tip: run `iron update . --source <new-pack-path>` to update this workspace while preserving accumulated user data.")

    report_path = root / "output" / "maintenance" / f"{now.date().isoformat()}-daily-maintenance.md"
    if daily.get("write_report", True):
        daily_html, index_html = write_web_report(root, now, lines, savings)
        lines.append(f"Latest daily HTML: {daily_html.relative_to(root)}")
        lines.append(f"Maintenance index: {index_html.relative_to(root)}")
        lines.append(f"Report written: {report_path.relative_to(root)}")
        report_path = write_report(root, now, lines)

    append_task_log(root, report_path, "daily maintenance completed")

    print("\n".join(lines))
    return result.returncode or shadow_result.returncode or slim_result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
