"""Command line interface for Iron Agent."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from . import __version__
from .core import (
    PACK_ROOT,
    apply_candidate,
    apply_template,
    check_workspace,
    clean_workspace,
    create_backup,
    doctor_checks,
    evolution_candidates,
    editor_adapter_status,
    generate_report,
    init_workspace,
    install_editor_adapters,
    list_editor_adapters,
    list_templates,
    move_memory_to_wiki,
    move_wiki_to_memory,
    new_domain_agent,
    patch_install_status,
    preview_template,
    read_config,
    read_install_status,
    read_task_entries,
    resolve_root,
    route_memory,
    search_memory,
    set_config_value,
)


app = typer.Typer(help="Iron Agent local workspace CLI.", no_args_is_help=True, invoke_without_command=True)
memory_app = typer.Typer(help="Browse and search layered memory.", no_args_is_help=True)
task_app = typer.Typer(help="Browse task-log.jsonl.", no_args_is_help=True)
config_app = typer.Typer(help="Manage Iron Agent config.", no_args_is_help=True)
template_app = typer.Typer(help="List, preview, and apply starter packs.", no_args_is_help=True)
agent_app = typer.Typer(help="Create domain agents.", no_args_is_help=True)
wiki_app = typer.Typer(help="Move wiki entries.", no_args_is_help=True)
editor_app = typer.Typer(help="Install editor and coding-agent adapters.", no_args_is_help=True)
app.add_typer(memory_app, name="memory")
app.add_typer(task_app, name="task")
app.add_typer(config_app, name="config")
app.add_typer(template_app, name="template")
app.add_typer(agent_app, name="agent")
app.add_typer(wiki_app, name="wiki")
app.add_typer(editor_app, name="editor")


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
    reset: bool = typer.Option(False, "--reset", help="Install but leave install_status at 0."),
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
        result = init_workspace(root, source=source.resolve() if source else PACK_ROOT, overwrite=overwrite, reset=reset)
        if template:
            result["template"] = apply_template(root, template)
    except Exception as exc:
        fail(str(exc), json_output)
    emit(result if json_output else f"Iron Agent installed to {root}", json_output)


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
    if read_install_status(root_path) == 0:
        patch_install_status(root_path, 1)
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
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Return the smallest relevant memory paths for a task."""
    paths = route_memory(task, resolve_root(root), limit=limit, include_cold=include_cold)
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


@editor_app.command("list")
def editor_list(json_output: bool = typer.Option(False, "--json", help="Emit JSON output.")) -> None:
    """List supported editor adapters."""
    adapters = list_editor_adapters()
    if json_output:
        emit({"adapters": adapters}, True)
    else:
        for item in adapters:
            typer.echo(f"{item['tool']}: {', '.join(item['targets'])}")


@editor_app.command("install")
def editor_install(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    tool: str = typer.Option("all", "--tool", help="claude, cursor, vscode, cline, roo, or all."),
    no_overwrite: bool = typer.Option(False, "--no-overwrite", help="Do not replace existing adapter files."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Install adapter instruction files into a workspace."""
    try:
        result = install_editor_adapters(resolve_root(root), tool=tool, overwrite=not no_overwrite)
    except Exception as exc:
        fail(str(exc), json_output)
    emit(result, json_output)


@editor_app.command("doctor")
def editor_doctor(
    root: Path = typer.Argument(Path("."), help="Iron Agent root."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Check editor adapter installation state."""
    status = editor_adapter_status(resolve_root(root))
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
