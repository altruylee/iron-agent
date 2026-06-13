param(
    [Parameter(Mandatory = $true)]
    [string]$Target,
    [string]$Source = $PSScriptRoot,
    [switch]$Overwrite,
    [switch]$SkipScheduler,
    [switch]$SkipCodexAutomation,
    [switch]$DryRun,
    [switch]$Portable
)

$ErrorActionPreference = "Stop"

$python = (Get-Command python -ErrorAction Stop).Source
$argsList = @(
    (Join-Path $Source "install.py"),
    "--source", $Source,
    "--target", $Target
)

if ($Overwrite) {
    $argsList += "--overwrite"
}
if ($SkipScheduler) {
    $argsList += "--skip-scheduler"
}
if ($SkipCodexAutomation) {
    $argsList += "--skip-codex-automation"
}
if ($DryRun) {
    $argsList += "--dry-run"
}
if ($Portable) {
    $argsList += "--portable"
}

& $python @argsList
