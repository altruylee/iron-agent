"""Command line interface for Iron Agent."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from . import __version__
from .core import (
    PACK_ROOT,
    apply_candidate,
    apply_template,
    automation_status,
    check_workspace,
    clean_workspace,
    capture_conversation,
    create_backup,
    doctor_checks,
    evolution_candidates,
    agent_adapter_status,
    generate_report,
    init_workspace,
    install_agent_adapters,
    install_automation,
    list_agent_adapters,
    list_templates,
    move_memory_to_wiki,
    move_wiki_to_memory,
    new_domain_agent,
    preview_template,
    read_config,
    read_install_status,
    read_task_entries,
    resolve_root,
    route_memory,
    search_memory,
    set_config_value,
    update_workspace,
)


app = typer.Typer(help="Iron Agent local workspace CLI.", no_args_is_help=True, invoke_without_command=True)
memory_app = typer.Typer(help="Browse and search layered memory.", no_args_is_help=True)
task_app = typer.Typer(help="Browse task-log.jsonl.", no_args_is_help=True)
config_app = typer.Typer(help="Manage Iron Agent config.", no_args_is_help=True)
template_app = typer.Typer(help="List, preview, and apply starter packs.", no_args_is_help=True)
agent_app = typer.Typer(help="Create domain agents.", no_args_is_help=True)
wiki_app = typer.Typer(help="Move wiki entries.", no_args_is_help=True)
adapter_app = typer.Typer(help="Install coding-agent adapters.", no_args_is_help=True)
automation_app = typer.Typer(help="Install silent background maintenance.", no_args_is_help=True)
app.add_typer(memory_app, name="memory")
app.add_typer(task_app, name="task")
app.add_typer(config_app, name="config")
app.add_typer(template_app, name="template")
app.add_typer(agent_app, name="agent")
app.add_typer(wiki_app, name="wiki")
app.add_typer(adapter_app, name="adapter")
app.add_typer(automation_app, name="automation")


def emit(data: object, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if isinstance(data, list):
        for item in data:
            typer.echo(item)
    elif isinstance(data, dict):
        for key, value in data.items():
            typer.echo(f"{key}: {value}")
    else:
        typer.echo(str(data))


def fail(message: str, json_output: bool = False, code: int = 1) -> None:
    if json_output:
        emit({"ok": False, "error": message}, True)
    else:
        typer.echo(message, err=True)
    raise typer.Exit(code)


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def init(
    target: Path = typer.Argument(..., help="Target folder for the workspace."),
    source: Optional[Path] = typer.Option(None, "--source", help="Source Iron Agent pack root."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Replace target if it already contains files."),
    reset: bool = typer.Option(False, "--reset", help="Compatibility option; installs now keep install_status at 0 by default."),
    complete: bool = typer.Option(False, "--complete", help="Advanced: mark install_status as 1 immediately."),
    status: bool = typer.Option(False, "--status", help="Only show install_status for target."),
    template: Optional[str] = typer.Option(None, "--template", help="Apply starter pack template."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Install an Iron Agent workspace."""
    root = resolve_root(target)
    if status:
        emit({"target": str(root), "install_status": read_install_status(root)}, json_output)
        return
    try:
        result = init_workspace(root, source=source.resolve() if source else PACK_ROOT, overwrite=overwrite, complete=complete and not reset)
        if template:
            result["template"] = apply_template(root, template)
    except Exception as exc:
        fail(str(exc), json_output)
    if json_output:
        emit(result, True)
    else:
        typer.echo(f"Iron Agent copied to {root}")
        typer.echo("install_status remains 0. Open this folder in Codex and say: 初始化 Iron Agent")
        typer.echo(f"Start file: {root / 'OPEN_ME_FIRST.md'}")


@app.command()
def check(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Validate release and manifest integrity."""
    try:
        result = check_workspace(resolve_root(root))
    except Exception as exc:
        fail(str(exc), json_output)
    if json_output:
        emit(result, True)
    else:
        if result["ok"]:
            typer.echo("Iron Agent workspace OK")
        else:
            if result["missing_required"]:
                typer.echo("Missing required files:")
                for item in result["missing_required"]:
                    typer.echo(f"- {item}")
            if result["local_only_values"]:
                typer.echo("Local-only values:")
                for item in result["local_only_values"]:
                    typer.echo(f"- {item}")
    if not result["ok"]:
        raise typer.Exit(1)


@app.command()
def report(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Generate an evolution report."""
    try:
        path = generate_report(resolve_root(root))
    except Exception as exc:
        fail(str(exc), json_output)
    emit({"report": str(path)} if json_output else str(path), json_output)


@app.command()
def clean(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    apply: bool = typer.Option(False, "--apply", help="Apply cleanup instead of dry run."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Clean runtime state before release."""
    try:
        actions = clean_workspace(resolve_root(root), apply=apply)
    except Exception as exc:
        fail(str(exc), json_output)
    if json_output:
        emit({"applied": apply, "actions": actions}, True)
    elif actions:
        emit(actions, False)
        if not apply:
            typer.echo("Dry run only. Re-run with --apply to clean.")
    else:
        typer.echo("Nothing to clean")


@app.command()
def doctor(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    fix: bool = typer.Option(False, "--fix", help="Repair reversible problems."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Run environment and workspace diagnostics."""
    root_path = resolve_root(root)
    results = doctor_checks(root_path, fix=fix)
    has_fail = any(item.status == "FAIL" for item in results)
    if json_output:
        emit({"ok": not has_fail, "checks": [item.to_dict() for item in results]}, True)
    else:
        for item in results:
            typer.echo(f"[{item.status}] {item.name}: {item.message}")
            if item.fix and item.status == "FAIL":
                typer.echo(f"  fix: {item.fix}")
    if has_fail:
        raise typer.Exit(1)


@app.command()
def evolve(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    interactive: bool = typer.Option(False, "--interactive", help="Show review-oriented next steps."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview candidate apply actions."),
    apply_all: bool = typer.Option(False, "--apply-all", help="Apply all matching candidates."),
    candidate_type: Optional[str] = typer.Option(None, "--type", help="Candidate type filter."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Trigger a manual evolution report."""
    root_path = resolve_root(root)
    report_path = generate_report(root_path)
    candidates = evolution_candidates(root_path)
    if candidate_type:
        candidates = [item for item in candidates if item.get("type") == candidate_type]
    applied = []
    if apply_all:
        applied = [apply_candidate(root_path, item, dry_run=dry_run) for item in candidates]
    result = {
        "report": str(report_path),
        "interactive": interactive,
        "candidates": candidates,
        "applied": applied,
        "next": [
            "Review repeated tasks with count >= 3.",
            "Promote stable workflows into system/skills/*.md.",
            "Move durable facts into workspace/memory/semantic/.",
        ],
    }
    if json_output:
        emit(result, True)
    else:
        typer.echo(f"Generated: {report_path}")
        if interactive:
            typer.echo(f"Evolution candidates found: {len(candidates)}")
            for index, item in enumerate(candidates, start=1):
                typer.echo(f"[{index}] {item['type']}: {item['title']} ({item['hits']} hits)")
                typer.echo(f"    Preview: {item['preview']}")
                if dry_run:
                    typer.echo("    Dry run: no files changed")
            for item in result["next"]:
                typer.echo(f"- {item}")


@app.command()
def quickstart(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Run the shortest local quickstart verification."""
    root_path = resolve_root(root)
    report_path = generate_report(root_path)
    result = {
        "ok": True,
        "root": str(root_path),
        "report": str(report_path),
        "next": "Open QUICKSTART.md and examples/end-to-end-demo/README.md",
    }
    emit(result if json_output else f"Quickstart OK. Report: {report_path}", json_output)


@app.command()
def backup(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    target: Optional[Path] = typer.Option(None, "--target", help="Backup directory."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Create a local workspace backup."""
    try:
        archive = create_backup(resolve_root(root), target.resolve() if target else None)
    except Exception as exc:
        fail(str(exc), json_output)
    emit({"archive": str(archive)} if json_output else str(archive), json_output)


@app.command()
def capture(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    file: Optional[Path] = typer.Option(None, "--file", help="Chat transcript or notes file to extract candidates from."),
    text: Optional[str] = typer.Option(None, "--text", help="Inline text to extract candidates from."),
    title: Optional[str] = typer.Option(None, "--title", help="Short title for this capture."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview extraction without writing files."),
    no_maintenance: bool = typer.Option(False, "--no-maintenance", help="Skip daily maintenance after capture."),
    keep_source: bool = typer.Option(False, "--keep-source", help="Keep the source chat file after successful capture."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Manually extract stable memory candidates from user-provided conversation text."""
    root_path = resolve_root(root)
    default_file = root_path / "today-chat.md"
    file_path = file.resolve() if file else default_file
    capture_title = title or f"{datetime.now().date().isoformat()} daily chat"
    if not text and not file_path.exists():
        fail(f"Default capture file not found: {file_path}. Create today-chat.md or use --file/--text.", json_output)
    try:
        content = text or file_path.read_text(encoding="utf-8", errors="replace")
        result = capture_conversation(root_path, content, title=capture_title, apply=not dry_run)
        maintenance_result = None
        if not dry_run and not no_maintenance:
            maintenance_script = root_path / "system" / "scripts" / "daily_maintenance.py"
            maintenance_result = subprocess.run(
                [sys.executable, str(maintenance_script), "--root", str(root_path), "--force"],
                text=True,
                capture_output=True,
                check=False,
            )
            result["maintenance"] = {
                "returncode": maintenance_result.returncode,
                "stdout": maintenance_result.stdout.strip(),
                "stderr": maintenance_result.stderr.strip(),
            }
        if not dry_run and not text and not keep_source and file_path.exists():
            file_path.unlink()
            result["source_removed"] = str(file_path)
        else:
            result["source_removed"] = ""
    except Exception as exc:
        fail(str(exc), json_output)
    if json_output:
        emit(result, True)
        return
    action = "previewed" if dry_run else "captured"
    typer.echo(f"Conversation {action}: {result['digest']}")
    typer.echo(f"Stable candidates: {result['candidate_count']}")
    if result["memory_candidates"]:
        typer.echo(f"Memory candidate review: {result['memory_candidates']}")
    typer.echo("Raw chat text was not stored.")
    if result.get("source_removed"):
        typer.echo(f"Source chat file removed: {result['source_removed']}")
    if not dry_run and not no_maintenance:
        maintenance = result.get("maintenance") or {}
        typer.echo("Daily maintenance: OK" if maintenance.get("returncode") == 0 else "Daily maintenance: FAILED")
        if maintenance.get("stdout"):
            typer.echo(maintenance["stdout"])
        if maintenance.get("stderr"):
            typer.echo(maintenance["stderr"])


@app.command()
def update(
    root: Path = typer.Argument(Path("."), help="Existing Iron Agent workspace to update."),
    source: Optional[Path] = typer.Option(None, "--source", help="New Iron Agent pack root. Defaults to this installed CLI package."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview files without changing the workspace."),
    no_backup: bool = typer.Option(False, "--no-backup", help="Skip automatic backup before applying."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Update an existing workspace while preserving accumulated user data."""
    try:
        result = update_workspace(
            resolve_root(root),
            source=source.resolve() if source else None,
            apply=not dry_run,
            backup=not no_backup,
        )
    except Exception as exc:
        fail(str(exc), json_output)
    if json_output:
        emit(result, True)
        return
    action = "previewed" if dry_run else "updated"
    typer.echo(f"Iron Agent workspace {action}: {result['root']}")
    typer.echo(f"Source: {result['source']}")
    if result["backup"]:
        typer.echo(f"Backup: {result['backup']}")
    typer.echo(f"Core files: {result['updated_count']}")
    typer.echo(f"Preserved user files: {result['preserved_count']}")
    if not dry_run:
        typer.echo("Health check: OK" if result["ok"] else "Health check: FAILED")
        typer.echo(f"install_status: {result['install_status']}")
        if result["install_status_fixed"]:
            typer.echo("install_status repaired by iron update")
        if result["agent_refresh_request"]:
            typer.echo(f"Agent refresh request: {result['agent_refresh_request']}")
        if result["agent_refresh_instruction"]:
            typer.echo("Current chat refresh prompt:")
            typer.echo(result["agent_refresh_instruction"])
        typer.echo("Next: python system/scripts/daily_maintenance.py --root . --force")


@app.command("index")
def index_memory(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Rebuild the local semantic memory index."""
    root_path = resolve_root(root)
    script = root_path / "system" / "scripts" / "memory_router.py"
    cmd = [sys.executable, str(script), "--root", str(root_path), "--rebuild-index"]
    if json_output:
        cmd.append("--json")
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.stdout:
        typer.echo(result.stdout.rstrip())
    if result.stderr:
        typer.echo(result.stderr.rstrip(), err=True)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@app.command("route")
def route(
    task: str = typer.Argument(..., help="Task or topic text."),
    root: Path = typer.Option(Path("."), "--root", help="Iron Agent root."),
    limit: int = typer.Option(5, "--limit", "--top-k", help="Maximum memory paths."),
    include_cold: bool = typer.Option(False, "--include-cold", help="Allow cold archive hits."),
    no_semantic: bool = typer.Option(False, "--no-semantic", help="Use keyword routing only."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Route a task to the smallest relevant memory paths."""
    root_path = resolve_root(root)
    script = root_path / "system" / "scripts" / "memory_router.py"
    cmd = [sys.executable, str(script), "--root", str(root_path), "--task", task, "--limit", str(limit)]
    if not no_semantic:
        cmd.append("--semantic")
    if include_cold:
        cmd.append("--include-cold")
    if json_output:
        cmd.append("--json")
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.stdout:
        typer.echo(result.stdout.rstrip())
    if result.stderr:
        typer.echo(result.stderr.rstrip(), err=True)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@app.command()
def web(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    port: int = typer.Option(8765, "--port", help="Local HTTP port."),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open default browser."),
) -> None:
    """Start the local Web UI."""
    from .web import serve

    serve(root, port=port, open_browser=open_browser)


@memory_app.command("route")
def memory_route(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    task: str = typer.Argument(..., help="Task or topic text."),
    limit: int = typer.Option(5, "--limit", help="Maximum memory paths."),
    include_cold: bool = typer.Option(False, "--include-cold", help="Allow cold archive hits."),
    semantic: bool = typer.Option(False, "--semantic", help="Use local semantic index before keyword fallback."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Return the smallest relevant memory paths for a task."""
    root_path = resolve_root(root)
    if semantic:
        script = root_path / "system" / "scripts" / "memory_router.py"
        cmd = [sys.executable, str(script), "--root", str(root_path), "--task", task, "--limit", str(limit), "--semantic"]
        if include_cold:
            cmd.append("--include-cold")
        if json_output:
            cmd.append("--json")
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if result.stdout:
            typer.echo(result.stdout.rstrip())
        if result.stderr:
            typer.echo(result.stderr.rstrip(), err=True)
        if result.returncode != 0:
            raise typer.Exit(result.returncode)
        return
    paths = route_memory(task, root_path, limit=limit, include_cold=include_cold)
    if json_output:
        emit({"paths": paths, "matched": bool(paths)}, True)
    elif paths:
        emit(paths, False)
    else:
        typer.echo("[未命中：按新内容正常处理]")


@memory_app.command("slim")
def memory_slim(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    apply: bool = typer.Option(False, "--apply", help="Create missing hot/warm/cold indexes."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Check low-token memory index limits."""
    root_path = resolve_root(root)
    script = root_path / "system" / "scripts" / "memory_index_maintenance.py"
    cmd = [sys.executable, str(script), "--root", str(root_path)]
    if apply:
        cmd.append("--apply")
    if json_output:
        cmd.append("--json")
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.stdout:
        typer.echo(result.stdout.rstrip())
    if result.stderr:
        typer.echo(result.stderr.rstrip(), err=True)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@memory_app.command("search")
def memory_search(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    query: str = typer.Argument(..., help="Search query."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Search Markdown memory files."""
    results = search_memory(resolve_root(root), query)
    if json_output:
        emit({"results": results}, True)
    else:
        for item in results:
            typer.echo(f"{item['path']} ({item['matches']})")


@memory_app.command("move-to-wiki")
def memory_move_to_wiki(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    source: str = typer.Argument(..., help="Memory file path relative to root."),
    slug: str = typer.Option(..., "--slug", help="Wiki concept slug."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Copy a memory file into wiki/concepts with a reversible move log."""
    try:
        result = move_memory_to_wiki(resolve_root(root), source, slug, apply=not dry_run)
    except Exception as exc:
        fail(str(exc), json_output)
    emit(result, json_output)


@task_app.command("list")
def task_list(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    limit: int = typer.Option(20, "--limit", help="Maximum entries to show."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """List recent task log entries."""
    entries = read_task_entries(resolve_root(root))[-limit:]
    if json_output:
        emit({"tasks": entries}, True)
    else:
        for entry in entries:
            status = "invalid" if entry.get("invalid") else entry.get("type", "unknown")
            typer.echo(f"{entry.get('index')}: {entry.get('task', entry.get('raw', ''))} [{status}]")


@task_app.command("show")
def task_show(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    index: int = typer.Argument(..., help="1-based task index."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Show one task log entry."""
    entries = read_task_entries(resolve_root(root))
    match = next((entry for entry in entries if entry.get("index") == index), None)
    if not match:
        fail(f"Task not found: {index}", json_output, code=1)
    emit(match, json_output)


@config_app.command("get")
def config_get(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    key: Optional[str] = typer.Argument(None, help="Optional dotted key."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Read config values."""
    config = read_config(resolve_root(root))
    if key:
        value = config.get(key.split(".", 1)[1] if key.startswith("evolution.") else key)
        emit({"key": key, "value": value} if json_output else value, json_output)
    else:
        emit(config, json_output)


@config_app.command("set")
def config_set(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    key: str = typer.Argument(..., help="Dotted key, for example evolution.friction_threshold."),
    value: str = typer.Argument(..., help="New value."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Set config values."""
    try:
        config = set_config_value(resolve_root(root), key, value)
    except Exception as exc:
        fail(str(exc), json_output)
    emit(config, json_output)


@template_app.command("list")
def template_list(json_output: bool = typer.Option(False, "--json", help="Emit JSON output.")) -> None:
    """List starter packs."""
    templates = list_templates()
    if json_output:
        emit({"templates": templates}, True)
    else:
        for item in templates:
            typer.echo(f"{item['name']}: {item['summary']}")


@template_app.command("preview")
def template_preview(
    name: str = typer.Argument(..., help="Template name."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Preview a starter pack."""
    try:
        preview = preview_template(name)
    except Exception as exc:
        fail(str(exc), json_output)
    if json_output:
        emit(preview, True)
    else:
        typer.echo(preview["readme"])
        typer.echo("Files:")
        for item in preview["files"]:
            typer.echo(f"- {item}")


@template_app.command("apply")
def template_apply(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    name: str = typer.Argument(..., help="Template name."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Apply a starter pack to an existing workspace."""
    try:
        result = apply_template(resolve_root(root), name)
    except Exception as exc:
        fail(str(exc), json_output)
    emit(result, json_output)


@agent_app.command("new")
def agent_new(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    name: str = typer.Argument(..., help="New domain agent folder name."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Replace existing agent folder."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Create a domain agent from the formal template."""
    try:
        result = new_domain_agent(resolve_root(root), name, overwrite=overwrite)
    except Exception as exc:
        fail(str(exc), json_output)
    emit(result, json_output)


@wiki_app.command("move-to-memory")
def wiki_move_to_memory(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    source: str = typer.Argument(..., help="Wiki file path relative to root."),
    target: str = typer.Option(..., "--target", help="Memory file target path relative to root."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Copy a wiki file into memory with a reversible move log."""
    try:
        result = move_wiki_to_memory(resolve_root(root), source, target, apply=not dry_run)
    except Exception as exc:
        fail(str(exc), json_output)
    emit(result, json_output)


@adapter_app.command("list")
def adapter_list(json_output: bool = typer.Option(False, "--json", help="Emit JSON output.")) -> None:
    """List supported agent adapters."""
    adapters = list_agent_adapters()
    if json_output:
        emit({"adapters": adapters}, True)
    else:
        for item in adapters:
            typer.echo(f"{item['tool']}: {', '.join(item['targets'])}")


@adapter_app.command("install")
def adapter_install(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    tool: str = typer.Option("all", "--tool", help="claude, workbuddy, or all."),
    no_overwrite: bool = typer.Option(False, "--no-overwrite", help="Do not replace existing adapter files."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Install agent adapter instruction files into a workspace."""
    try:
        result = install_agent_adapters(resolve_root(root), tool=tool, overwrite=not no_overwrite)
    except Exception as exc:
        fail(str(exc), json_output)
    emit(result, json_output)


@adapter_app.command("doctor")
def adapter_doctor(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Check agent adapter installation state."""
    status = agent_adapter_status(resolve_root(root))
    ok = all(item["ok"] for item in status)
    if json_output:
        emit({"ok": ok, "adapters": status}, True)
    else:
        for item in status:
            typer.echo(f"[{'OK' if item['ok'] else 'MISSING'}] {item['tool']}")
            for target in item["targets"]:
                typer.echo(f"  {target['path']}: {target['exists']}")
    if not ok:
        raise typer.Exit(1)


@automation_app.command("install")
def automation_install(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    tool: str = typer.Option("all", "--tool", help="claude, workbuddy, or all."),
    time: str = typer.Option("23:30", "--time", help="Daily maintenance time, HH:MM."),
    apply: bool = typer.Option(False, "--apply", help="Create the OS scheduled task."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Install silent agent adapters and daily background maintenance."""
    try:
        result = install_automation(resolve_root(root), tool=tool, time=time, apply=apply)
    except Exception as exc:
        fail(str(exc), json_output)
    if json_output:
        emit(result, True)
    else:
        typer.echo(f"Adapters installed: {len(result['adapters'])}")
        typer.echo(f"Daily maintenance: {result['task_name']} at {result['time']}")
        typer.echo(f"State: {result['state']}")
        if result.get("note"):
            typer.echo(result["note"])
        if not result.get("ok", False):
            raise typer.Exit(1)


@automation_app.command("status")
def automation_doctor(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Show silent automation setup status."""
    result = automation_status(resolve_root(root))
    if json_output:
        emit(result, True)
    else:
        typer.echo(f"state: {result['state_path']}")
        typer.echo(f"ok: {result['ok']}")
        for item in result["adapters"]:
            typer.echo(f"{item['tool']}: {'OK' if item['ok'] else 'MISSING'}")
    if not result["ok"]:
        raise typer.Exit(1)
