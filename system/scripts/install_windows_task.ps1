param(
    [string]$Root = "",
    [string]$TaskName = "IronAgentDailyMaintenance",
    [string]$At = "02:30",
    [switch]$RunNow,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Join-Path $PSScriptRoot "..\.."
}

$resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
$maintenanceScript = Join-Path $resolvedRoot "system\scripts\daily_maintenance.py"
$statePath = Join-Path $resolvedRoot "workspace\meta\scheduled-task-state.json"

if (-not (Test-Path -LiteralPath $maintenanceScript)) {
    throw "Missing maintenance script: $maintenanceScript"
}

$python = (Get-Command python -ErrorAction Stop).Source
$argument = "`"$maintenanceScript`" --root `"$resolvedRoot`""
$description = "Iron Agent local preflight maintenance. Prepares memory candidates and trigger state before Codex automation."

$summary = [ordered]@{
    task_name = $TaskName
    trigger = "Daily at $At"
    user = $env:USERNAME
    python = $python
    script = $maintenanceScript
    root = $resolvedRoot
    action = "$python $argument"
    run_now = [bool]$RunNow
    dry_run = [bool]$DryRun
    next_step = "Create Codex automation to run AI shadow review after this task, default 02:45."
}

if ($DryRun) {
    $summary | ConvertTo-Json -Depth 4
    exit 0
}

$time = [datetime]::ParseExact($At, "HH:mm", [System.Globalization.CultureInfo]::InvariantCulture)
$action = New-ScheduledTaskAction -Execute $python -Argument $argument -WorkingDirectory $resolvedRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $time
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfIdle `
    -IdleDuration (New-TimeSpan -Minutes 10) `
    -IdleWaitTimeout (New-TimeSpan -Hours 2) `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description $description `
    -Force | Out-Null

$state = [ordered]@{
    task_name = $TaskName
    installed_at = (Get-Date).ToString("s")
    trigger = "Daily at $At"
    user = $env:USERNAME
    python = $python
    root = $resolvedRoot
    script = $maintenanceScript
    run_only_if_idle = $true
    codex_automation_expected = $true
    codex_automation_default_time = "02:45"
}

$stateDir = Split-Path -Parent $statePath
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
$state | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8

if ($RunNow) {
    Start-ScheduledTask -TaskName $TaskName
}

$state | ConvertTo-Json -Depth 4
