"""Core operations for the Iron Agent CLI."""

from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACK_ROOT = Path(__file__).resolve().parents[1]

RUNTIME_DIRS = [
    "inbox",
    "output",
    "output/research",
    "output/maintenance",
    "output/evolution",
    "output/skill-audits",
    "watchlists",
    "hypotheses",
    "tools",
    "tools/packages",
    "backups",
    "wiki/raw",
    "wiki/sources",
    "wiki/entities",
    "wiki/concepts",
    "wiki/explorations",
    "workspace/meta",
    "workspace/memory/hot",
    "workspace/memory/warm",
    "workspace/memory/cold",
]

RUNTIME_FILES = [
    "workspace/meta/task-log.jsonl",
]

TEMPLATE_ROOT = PACK_ROOT / "templates"
EVOLUTION_CONFIG = "config/evolution.yaml"
MOVE_LOG = "workspace/meta/wiki-memory-moves.jsonl"
ADAPTER_ROOT = PACK_ROOT / "adapters"
EDITOR_ADAPTERS = {
    "claude": [
        ("adapters/claude/CLAUDE.md", "CLAUDE.md"),
        ("adapters/claude/.claude/settings.json", ".claude/settings.json"),
    ],
    "cursor": [
        ("adapters/cursor/.cursor/rules/iron-agent.mdc", ".cursor/rules/iron-agent.mdc"),
        ("adapters/cursor/.cursor/rules/iron-agent-automation.mdc", ".cursor/rules/iron-agent-automation.mdc"),
    ],
    "vscode": [
        ("adapters/vscode/.github/copilot-instructions.md", ".github/copilot-instructions.md"),
        ("adapters/vscode/.vscode/tasks.json", ".vscode/tasks.json"),
    ],
    "cline": [("adapters/cline/.clinerules", ".clinerules")],
    "roo": [("adapters/roo/.roo/rules/iron-agent.md", ".roo/rules/iron-agent.md")],
}

EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", "iron.egg-info"}
EXCLUDE_PREFIXES = {
    "output",
    "backups",
    "workspace/meta/task-log.jsonl",
    "workspace/meta/maintenance-state.json",
    "workspace/meta/memory-candidates.md",
    "workspace/meta/scheduled-task-state.json",
    "workspace/meta/codex-automation-state.md",
    "workspace/meta/codex-automation-trigger.json",
    "workspace/meta/package-registry.json",
}

LOCAL_ONLY_PATTERNS = [
    re.compile(r"\b[A-Za-z]:\\Users\\", re.IGNORECASE),
    re.compile(r"\bD:\\DOC\\", re.IGNORECASE),
    re.compile(r"iron-agent-shadow" + r"-review", re.IGNORECASE),
]

TOPICS = {
    "finance-settlement": {
        "keywords": ["财务结算", "结算", "对账", "账期", "付款", "收款", "发票", "finance", "settlement"],
        "paths": [
            "workspace/memory/episodes/finance/INDEX.md",
            "workspace/memory/semantic/sops/finance-settlement.md",
        ],
    },
    "user-registration": {
        "keywords": ["用户注册", "注册", "登录", "开户", "验证码", "账号", "onboarding", "registration"],
        "paths": [
            "workspace/memory/episodes/user-registration/INDEX.md",
            "workspace/memory/semantic/sops/user-registration.md",
        ],
    },
    "development": {
        "keywords": ["开发", "代码", "bug", "测试", "重构", "repo", "code", "test", "refactor"],
        "paths": [
            "packs/domain-agents/INDEX.md",
            "workspace/memory/episodes/development/INDEX.md",
        ],
    },
}


def load_memory_index(root: Path) -> dict[str, list[str]]:
    index_path = root / "workspace" / "memory" / "index.json"
    if not index_path.exists():
        return {key: value["paths"] for key, value in TOPICS.items()}
    data = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    result: dict[str, list[str]] = {}
    for topic, paths in data.items():
        if isinstance(paths, list):
            result[str(topic)] = [str(path) for path in paths]
    return result


def score_memory_topic(task: str, topic: str) -> int:
    lowered = task.lower()
    score = 0
    if topic.lower() in lowered:
        score += 10
    for token in topic.lower().replace("-", " ").split():
        if token and token in lowered:
            score += 2
    for char in topic:
        if "\u4e00" <= char <= "\u9fff" and char in task:
            score += 1
    return score


@dataclass
class CheckResult:
    name: str
    status: str
    message: str
    fix: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "fix": self.fix,
        }


def resolve_root(root: str | Path) -> Path:
    return Path(root).expanduser().resolve()


def ensure_iron_root(root: Path) -> None:
    if not (root / "AGENTS.md").exists() or not (root / "manifest.json").exists():
        raise ValueError(f"Not an Iron Agent root: {root}")


def should_skip_copy(src_root: Path, path: Path) -> bool:
    rel = path.relative_to(src_root).as_posix()
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    return any(rel == prefix or rel.startswith(f"{prefix}/") for prefix in EXCLUDE_PREFIXES)


def copy_pack(source: Path, target: Path, overwrite: bool) -> None:
    if target == source or source in target.parents:
        raise ValueError("Target must be outside the source Iron Agent repository.")
    if target.exists() and any(target.iterdir()) and not overwrite:
        raise ValueError(f"Target is not empty: {target}. Use --overwrite to replace files.")
    if target.exists() and overwrite:
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    for path in source.rglob("*"):
        if should_skip_copy(source, path):
            continue
        rel = path.relative_to(source)
        dest = target / rel
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)

    for rel in RUNTIME_DIRS:
        (target / rel).mkdir(parents=True, exist_ok=True)
    for rel in RUNTIME_FILES:
        file_path = target / rel
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch(exist_ok=True)


def patch_install_status(root: Path, status: int, installer_agent: str = "iron-cli") -> bool:
    agents_path = root / "AGENTS.md"
    if not agents_path.exists():
        return False
    text = agents_path.read_text(encoding="utf-8")
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    replacements = {
        r"- install_status: `\d+`": f"- install_status: `{status}`",
        r"- installed_at:.*": f"- installed_at: {now if status == 1 else ''}",
        r"- installer_agent:.*": f"- installer_agent: {installer_agent if status == 1 else ''}",
        r"- profile_version: `\d+`": f"- profile_version: `{1 if status == 1 else 0}`",
    }
    updated = text
    for pattern, replacement in replacements.items():
        updated = re.sub(pattern, replacement, updated)
    if updated == text:
        return False
    agents_path.write_text(updated, encoding="utf-8")
    return True


def read_install_status(root: Path) -> int | None:
    agents_path = root / "AGENTS.md"
    if not agents_path.exists():
        return None
    match = re.search(r"- install_status: `(\d+)`", agents_path.read_text(encoding="utf-8", errors="replace"))
    return int(match.group(1)) if match else None


def init_workspace(target: Path, source: Path | None = None, overwrite: bool = False, reset: bool = False) -> dict[str, Any]:
    source_root = source or PACK_ROOT
    copy_pack(source_root, target, overwrite=overwrite)
    patch_install_status(target, 0 if reset else 1)
    return {"target": str(target), "source": str(source_root), "install_status": read_install_status(target)}


def merge_tree(source: Path, target: Path, overwrite: bool = True) -> list[str]:
    copied: list[str] = []
    for path in source.rglob("*"):
        rel = path.relative_to(source)
        dest = target / rel
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        if dest.exists() and not overwrite:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        copied.append(rel.as_posix())
    return copied


def apply_template(root: Path, name: str, overwrite: bool = True) -> dict[str, Any]:
    template = TEMPLATE_ROOT / name
    if not template.exists():
        raise ValueError(f"Unknown template: {name}")
    copied = merge_tree(template, root, overwrite=overwrite)
    return {"template": name, "copied": copied}


def list_templates() -> list[dict[str, str]]:
    templates: list[dict[str, str]] = []
    if not TEMPLATE_ROOT.exists():
        return templates
    for path in sorted(TEMPLATE_ROOT.iterdir()):
        if path.is_dir():
            readme = path / "README.md"
            summary = ""
            if readme.exists():
                lines = [line.strip() for line in readme.read_text(encoding="utf-8", errors="replace").splitlines()]
                summary = next((line for line in lines if line and not line.startswith("#") and not line.startswith("-")), "")
            templates.append({"name": path.name, "summary": summary})
    return templates


def preview_template(name: str) -> dict[str, Any]:
    template = TEMPLATE_ROOT / name
    if not template.exists():
        raise ValueError(f"Unknown template: {name}")
    files = [path.relative_to(template).as_posix() for path in template.rglob("*") if path.is_file()]
    readme = template / "README.md"
    return {
        "name": name,
        "files": files,
        "readme": readme.read_text(encoding="utf-8", errors="replace") if readme.exists() else "",
    }


def load_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise ValueError("manifest.json is missing")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def required_files_from_manifest(root: Path) -> list[str]:
    manifest = load_manifest(root)
    required = manifest.get("required")
    if not isinstance(required, list):
        raise ValueError("manifest.json must contain a required list")
    return [str(item) for item in required]


def validate_manifest_required(root: Path) -> list[str]:
    return [rel for rel in required_files_from_manifest(root) if not (root / rel).exists()]


def scan_local_only_values(root: Path) -> list[str]:
    failures: list[str] = []
    skip_dirs = {".git", "__pycache__", "output", "backups", "tools", "iron.egg-info"}
    skip_files = {"system/scripts/release_check.py", "iron/core.py"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel in skip_files or any(part in skip_dirs for part in path.relative_to(root).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern in LOCAL_ONLY_PATTERNS:
            if pattern.search(text):
                failures.append(f"{rel}: {pattern.pattern}")
    return failures


def check_workspace(root: Path) -> dict[str, Any]:
    ensure_iron_root(root)
    missing = validate_manifest_required(root)
    local_only = scan_local_only_values(root)
    ok = not missing and not local_only
    return {
        "ok": ok,
        "missing_required": missing,
        "local_only_values": local_only,
        "root": str(root),
    }


def clean_workspace(root: Path, apply: bool = False) -> list[str]:
    ensure_iron_root(root)
    actions: list[str] = []
    runtime_dirs = ["output", "backups", "inbox", "wiki/raw", "wiki/sources", "wiki/entities", "wiki/concepts", "wiki/explorations"]
    state_files = [
        "workspace/meta/task-log.jsonl",
        "workspace/meta/maintenance-state.json",
        "workspace/meta/memory-candidates.md",
        "workspace/meta/scheduled-task-state.json",
        "workspace/meta/codex-automation-state.md",
        "workspace/meta/codex-automation-trigger.json",
        "workspace/meta/package-registry.json",
    ]
    for rel in runtime_dirs:
        path = root / rel
        if not path.exists():
            continue
        for child in path.iterdir():
            if child.name == ".gitkeep":
                continue
            actions.append(f"remove {child.relative_to(root).as_posix()}")
            if apply:
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    for rel in state_files:
        path = root / rel
        if not path.exists():
            continue
        if path.name == "task-log.jsonl":
            actions.append(f"truncate {rel}")
            if apply:
                path.write_text("", encoding="utf-8")
        else:
            actions.append(f"remove {rel}")
            if apply:
                path.unlink()
    return actions


def read_task_entries(root: Path) -> list[dict[str, Any]]:
    log_path = root / "workspace" / "meta" / "task-log.jsonl"
    if not log_path.exists():
        demo_log_path = root / "logs" / "task-log.jsonl"
        if demo_log_path.exists():
            log_path = demo_log_path
    if not log_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for index, line in enumerate(log_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            entry = {"index": index, "invalid": True, "raw": line}
        else:
            entry["index"] = index
        entries.append(entry)
    return entries


def route_memory(task: str, root: Path, limit: int = 5, include_cold: bool = False) -> list[str]:
    index = load_memory_index(root)
    ranked = sorted(
        ((topic, score_memory_topic(task, topic), paths) for topic, paths in index.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    matches: list[str] = []
    for _topic, score, paths in ranked:
        if score < 2:
            continue
        for item in paths:
            normalized = item.replace("\\", "/")
            if not include_cold and "/cold/" in normalized:
                continue
            if (root / item).exists():
                matches.append(item)
            if len(matches) >= limit:
                return list(dict.fromkeys(matches))
    return list(dict.fromkeys(matches))


def search_memory(root: Path, query: str) -> list[dict[str, Any]]:
    memory_root = root / "workspace" / "memory"
    if not memory_root.exists() and (root / "memory").exists():
        memory_root = root / "memory"
    if not memory_root.exists():
        return []
    lowered = query.lower()
    results: list[dict[str, Any]] = []
    for path in memory_root.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if lowered in text.lower() or lowered in path.as_posix().lower():
            results.append({
                "path": path.relative_to(root).as_posix(),
                "matches": text.lower().count(lowered) if lowered else 0,
            })
    return results


def generate_report(root: Path) -> Path:
    from collections import Counter

    entries = read_task_entries(root)
    thresholds = read_config(root, EVOLUTION_CONFIG)
    task_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()
    memory_candidates = 0
    for entry in entries:
        if entry.get("invalid"):
            continue
        task_counter[str(entry.get("task", "unknown"))] += 1
        type_counter[str(entry.get("type", "unknown"))] += 1
        memory_candidates += len(entry.get("memory_candidates", []))

    report_dir = root / "output" / "evolution"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / f"{datetime.now().strftime('%Y-%m-%d')}-evolution-report.md"
    lines = [
        "# Evolution Report",
        "",
        "## Directory",
        "",
        "- [Summary](#summary)",
        "- [Repeated Tasks](#repeated-tasks)",
        "- [Task Types](#task-types)",
        "- [Recommendations](#recommendations)",
        "",
        "## Summary",
        "",
        f"- Task entries observed: `{len(entries)}`",
        f"- Memory candidates observed: `{memory_candidates}`",
        f"- Candidate rule: repeated tasks >= `{thresholds.get('friction_threshold', 3)}` friction hits or commands >= `{thresholds.get('command_threshold', 5)}` uses.",
        f"- Minimum token saving: `{thresholds.get('min_token_saving', 100)}` tokens.",
        f"- Window: `{thresholds.get('window_days', 7)}` days.",
        "",
        "## Repeated Tasks",
        "",
    ]
    lines.extend(f"- `{task}`: {count}" for task, count in task_counter.most_common(20))
    lines += ["", "## Task Types", ""]
    lines.extend(f"- `{task_type}`: {count}" for task_type, count in type_counter.most_common())
    lines += [
        "",
        "## Recommendations",
        "",
        "- Promote repeated tasks into skills when the same task appears 3+ times.",
        "- Review memory candidates after maintenance runs.",
        "- Put domain-specific workflows in `packs/domain-agents/`.",
        "",
    ]
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def parse_scalar(value: str) -> Any:
    stripped = value.strip()
    if stripped.lower() == "true":
        return True
    if stripped.lower() == "false":
        return False
    try:
        return int(stripped)
    except ValueError:
        return stripped.strip('"').strip("'")


def format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def read_config(root: Path, rel: str = EVOLUTION_CONFIG) -> dict[str, Any]:
    path = root / rel
    if not path.exists():
        return {}
    data: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[key.strip()] = parse_scalar(value.split("#", 1)[0])
    return data


def write_config(root: Path, values: dict[str, Any], rel: str = EVOLUTION_CONFIG) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}: {format_scalar(value)}" for key, value in values.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def set_config_value(root: Path, dotted_key: str, value: str) -> dict[str, Any]:
    if not dotted_key.startswith("evolution."):
        raise ValueError("Only evolution.* config is supported in v0.3.0")
    key = dotted_key.split(".", 1)[1]
    config = read_config(root, EVOLUTION_CONFIG)
    config[key] = parse_scalar(value)
    write_config(root, config, EVOLUTION_CONFIG)
    return config


def evolution_candidates(root: Path) -> list[dict[str, Any]]:
    thresholds = read_config(root, EVOLUTION_CONFIG)
    friction_threshold = int(thresholds.get("friction_threshold", 3))
    entries = read_task_entries(root)
    friction_counts: dict[str, int] = {}
    command_counts: dict[str, int] = {}
    memory_candidates: list[str] = []
    for entry in entries:
        for item in entry.get("friction", []) if not entry.get("invalid") else []:
            friction_counts[item] = friction_counts.get(item, 0) + 1
        for item in entry.get("commands", []) if not entry.get("invalid") else []:
            command_counts[item] = command_counts.get(item, 0) + 1
        for item in entry.get("memory_candidates", []) if not entry.get("invalid") else []:
            memory_candidates.append(item)

    candidates: list[dict[str, Any]] = []
    for name, count in sorted(friction_counts.items(), key=lambda item: item[1], reverse=True):
        if count >= friction_threshold:
            candidates.append({
                "type": "NEW_SKILL",
                "title": name,
                "hits": count,
                "preview": f"Create a skill for repeated friction: {name}",
            })
    if memory_candidates:
        candidates.append({
            "type": "MEMORY_MOVE",
            "title": "Promote memory candidates",
            "hits": len(memory_candidates),
            "preview": "; ".join(memory_candidates[:5]),
        })
    if not candidates:
        candidates.append({
            "type": "SCHEMA_UPDATE",
            "title": "No threshold candidate",
            "hits": 0,
            "preview": "No candidate reached the configured threshold; review config/evolution.yaml.",
        })
    return candidates[: int(thresholds.get("max_candidates_per_run", 5))]


def apply_candidate(root: Path, candidate: dict[str, Any], dry_run: bool = True) -> dict[str, Any]:
    ctype = candidate.get("type")
    if ctype == "NEW_SKILL":
        slug = re.sub(r"[^a-z0-9]+", "-", str(candidate.get("title", "skill")).lower()).strip("-") or "skill"
        path = root / "system" / "skills" / f"{slug}.md"
        content = f"# {slug}\n\n## Directory\n\n- [Purpose](#purpose)\n\n## Purpose\n\n{candidate.get('preview')}\n"
        if not dry_run:
            path.write_text(content, encoding="utf-8")
        return {"type": ctype, "path": str(path), "dry_run": dry_run}
    if ctype == "MEMORY_MOVE":
        path = root / "workspace" / "memory" / "semantic" / "evolution-candidates.md"
        content = f"# Evolution Memory Candidates\n\n## Directory\n\n- [Candidates](#candidates)\n\n## Candidates\n\n- {candidate.get('preview')}\n"
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return {"type": ctype, "path": str(path), "dry_run": dry_run}
    return {"type": ctype, "dry_run": dry_run, "message": "No automatic apply action for this candidate type"}


def new_domain_agent(root: Path, name: str, overwrite: bool = False) -> dict[str, Any]:
    template = root / "packs" / "domain-agents" / "_template"
    if not template.exists():
        template = PACK_ROOT / "packs" / "domain-agents" / "_template"
    target = root / "packs" / "domain-agents" / name
    if target.exists() and not overwrite:
        raise ValueError(f"Domain agent exists: {target}")
    copied = merge_tree(template, target, overwrite=True)
    return {"name": name, "target": str(target), "copied": copied}


def log_move(root: Path, action: str, source: str, target: str, status: str) -> None:
    path = root / MOVE_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "action": action,
        "source": source,
        "target": target,
        "status": status,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def rel_path(value: str) -> Path:
    return Path(*value.replace("\\", "/").split("/"))


def move_memory_to_wiki(root: Path, source_rel: str, slug: str, apply: bool = True) -> dict[str, Any]:
    source = root / rel_path(source_rel)
    if not source.exists():
        raise ValueError(f"Memory file not found: {source_rel}")
    target = root / "wiki" / "concepts" / f"{slug}.md"
    if apply:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        log_move(root, "memory-to-wiki", source_rel, target.relative_to(root).as_posix(), "moved")
    return {"source": source_rel, "target": target.relative_to(root).as_posix(), "apply": apply}


def move_wiki_to_memory(root: Path, source_rel: str, target_rel: str, apply: bool = True) -> dict[str, Any]:
    source = root / rel_path(source_rel)
    if not source.exists():
        raise ValueError(f"Wiki file not found: {source_rel}")
    target = root / rel_path(target_rel)
    if apply:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        log_move(root, "wiki-to-memory", source_rel, target_rel, "moved")
    return {"source": source_rel, "target": target_rel, "apply": apply}


def read_move_log(root: Path) -> list[dict[str, Any]]:
    path = root / MOVE_LOG
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def list_editor_adapters() -> list[dict[str, Any]]:
    return [{"tool": tool, "targets": [target for _source, target in files]} for tool, files in EDITOR_ADAPTERS.items()]


def install_editor_adapters(root: Path, tool: str = "all", overwrite: bool = True) -> dict[str, Any]:
    tools = list(EDITOR_ADAPTERS) if tool == "all" else [tool]
    copied: list[str] = []
    for item in tools:
        if item not in EDITOR_ADAPTERS:
            raise ValueError(f"Unknown editor adapter: {item}")
        for source_rel, target_rel in EDITOR_ADAPTERS[item]:
            source = PACK_ROOT / source_rel
            target = root / rel_path(target_rel)
            if target.exists() and not overwrite:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target.relative_to(root).as_posix())
    return {"tool": tool, "copied": copied}


def editor_adapter_status(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tool, files in EDITOR_ADAPTERS.items():
        targets = []
        ok = True
        for _source, target_rel in files:
            path = root / rel_path(target_rel)
            exists = path.exists()
            ok = ok and exists
            targets.append({"path": target_rel, "exists": exists})
        rows.append({"tool": tool, "ok": ok, "targets": targets})
    return rows


def automation_task_name(root: Path) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", root.name).strip("-") or "workspace"
    return f"IronAgentDailyMaintenance-{slug}"


def daily_maintenance_command(root: Path) -> list[str]:
    script = root / "system" / "scripts" / "daily_maintenance.py"
    return [sys.executable, str(script), "--root", str(root)]


def install_automation(root: Path, tool: str = "all", time: str = "23:30", apply: bool = False) -> dict[str, Any]:
    ensure_iron_root(root)
    adapter_result = install_editor_adapters(root, tool=tool, overwrite=True)
    task_name = automation_task_name(root)
    command = daily_maintenance_command(root)
    state_path = root / "workspace" / "meta" / "scheduled-task-state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "ok": True,
        "applied": apply,
        "tool": tool,
        "adapters": adapter_result["copied"],
        "task_name": task_name,
        "time": time,
        "command": command,
        "scheduler": "windows-task-scheduler" if platform.system().lower() == "windows" else "external",
        "state": str(state_path),
    }
    if apply and platform.system().lower() == "windows":
        tr = f'cmd /c cd /d "{root}" && "{command[0]}" "{command[1]}" --root "{root}"'
        scheduled = subprocess.run(
            ["schtasks", "/Create", "/F", "/SC", "DAILY", "/ST", time, "/TN", task_name, "/TR", tr],
            text=True,
            capture_output=True,
            check=False,
        )
        result["scheduler_returncode"] = scheduled.returncode
        result["scheduler_stdout"] = scheduled.stdout.strip()
        result["scheduler_stderr"] = scheduled.stderr.strip()
        result["ok"] = scheduled.returncode == 0
    elif apply:
        result["ok"] = False
        result["note"] = "Automatic scheduler install is currently implemented for Windows. Use cron/systemd/launchd with the returned command."
    else:
        result["note"] = "Dry run only. Re-run with --apply to create the scheduled task."
    if apply:
        state_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def automation_status(root: Path) -> dict[str, Any]:
    state_path = root / "workspace" / "meta" / "scheduled-task-state.json"
    adapters = editor_adapter_status(root)
    state: dict[str, Any] | None = None
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {"error": "invalid scheduled-task-state.json"}
    return {
        "ok": bool(state_path.exists()) and all(item["ok"] for item in adapters),
        "state_path": str(state_path),
        "state": state,
        "adapters": adapters,
    }


def doctor_checks(root: Path, fix: bool = False) -> list[CheckResult]:
    results: list[CheckResult] = []
    py_ok = sys.version_info >= (3, 10)
    results.append(CheckResult("python-version", "OK" if py_ok else "FAIL", platform.python_version(), "Install Python 3.10+" if not py_ok else None))

    agents = root / "AGENTS.md"
    results.append(CheckResult("agents-md", "OK" if agents.exists() else "FAIL", "AGENTS.md present" if agents.exists() else "AGENTS.md missing"))

    status = read_install_status(root)
    if status == 1:
        results.append(CheckResult("install-status", "OK", "install_status is 1"))
    elif status == 0:
        if fix:
            patch_install_status(root, 1)
            results.append(CheckResult("install-status", "OK", "install_status changed from 0 to 1"))
        else:
            results.append(CheckResult("install-status", "WARN", "install_status is 0", "iron doctor . --fix"))
    else:
        results.append(CheckResult("install-status", "FAIL", "install_status not found", "Check AGENTS.md Installation State"))

    memory_index = root / "workspace" / "memory" / "INDEX.md"
    if not memory_index.exists() and fix:
        memory_index.parent.mkdir(parents=True, exist_ok=True)
        memory_index.write_text("# Memory Index\n\n## Directory\n\n- [Overview](#overview)\n\n## Overview\n\nNo memory entries yet.\n", encoding="utf-8")
    results.append(CheckResult("memory-index", "OK" if memory_index.exists() else "FAIL", "workspace/memory/INDEX.md present" if memory_index.exists() else "workspace/memory/INDEX.md missing", "iron doctor . --fix"))

    task_log = root / "workspace" / "meta" / "task-log.jsonl"
    if not task_log.exists() and fix:
        task_log.parent.mkdir(parents=True, exist_ok=True)
        task_log.touch()
    task_status = "OK" if task_log.exists() else "WARN"
    results.append(CheckResult("task-log", task_status, "task-log.jsonl present" if task_log.exists() else "task-log.jsonl missing; run the demo", "iron doctor . --fix"))

    skill = root / "codex-global-skill" / "SKILL.md"
    results.append(CheckResult("codex-global-skill", "OK" if skill.exists() else "FAIL", "codex-global-skill/SKILL.md present" if skill.exists() else "codex-global-skill/SKILL.md missing"))

    try:
        missing = validate_manifest_required(root)
    except Exception as exc:
        results.append(CheckResult("manifest", "FAIL", str(exc)))
    else:
        results.append(CheckResult("manifest", "OK" if not missing else "FAIL", "manifest required files present" if not missing else f"missing: {', '.join(missing[:8])}", "Restore missing files or reinstall Iron Agent"))

    domain_index = root / "packs" / "domain-agents" / "INDEX.md"
    results.append(CheckResult("domain-agents-index", "OK" if domain_index.exists() else "FAIL", "packs/domain-agents/INDEX.md present" if domain_index.exists() else "domain agent index missing"))

    path_ok = str(root).strip() != ""
    results.append(CheckResult("path", "OK" if path_ok else "FAIL", str(root)))

    if platform.system().lower() == "windows":
        schedule_state = root / "workspace" / "meta" / "scheduled-task-state.json"
        results.append(CheckResult("windows-scheduler", "OK" if schedule_state.exists() else "WARN", "scheduler state present" if schedule_state.exists() else "no Windows scheduled task state"))
    else:
        results.append(CheckResult("scheduler", "WARN", "cross-platform scheduler is planned for v0.4.0"))

    usage = shutil.disk_usage(root)
    enough = usage.free >= 500 * 1024 * 1024
    results.append(CheckResult("disk-space", "OK" if enough else "FAIL", f"free={usage.free // (1024 * 1024)}MB", "Free at least 500MB"))

    return results


def create_backup(root: Path, target: Path | None = None) -> Path:
    ensure_iron_root(root)
    backup_dir = target or (root / "backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    archive = backup_dir / f"iron-agent-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
    include = ["workspace", "config", "packs"]
    with tarfile.open(archive, "w:gz") as tar:
        for rel in include:
            path = root / rel
            if path.exists():
                tar.add(path, arcname=rel)
    return archive
