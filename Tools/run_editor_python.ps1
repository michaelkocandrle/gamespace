<#
.SYNOPSIS
    Runs a Python script headless inside the Unreal Editor for this project.

.DESCRIPTION
    Uses the pythonscript commandlet with PythonScriptPlugin enabled on the command line,
    so the .uproject does not need the plugin enabled. Content/Python is on sys.path, so
    scripts can `import gamespace_assets`.

    Refuses to run while an editor has the same project open: the open editor keeps its own
    in-memory copies of assets and would overwrite the script's changes on its next save.
    For that case, run the script from the editor instead (Tools > Execute Python Script,
    with the Python Editor Script Plugin enabled).

.EXAMPLE
    .\Tools\run_editor_python.ps1 Tools\Assets\make_debug_input.py
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Script,

    [string]$Project = (Join-Path $PSScriptRoot "..\gamespace.uproject"),

    [string]$EngineDir = "C:\Program Files\Epic Games\UE_5.8"
)

$ErrorActionPreference = "Stop"

$Project = (Resolve-Path $Project).Path
$Script = (Resolve-Path $Script).Path
$editorCmd = Join-Path $EngineDir "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"

# An editor started from the launcher or a shortcut carries the .uproject on its command line.
$projectName = [IO.Path]::GetFileName($Project)
$openEditors = Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor.exe'" |
    Where-Object { -not $_.CommandLine -or $_.CommandLine -like "*$projectName*" }
if ($openEditors) {
    $pids = ($openEditors | ForEach-Object ProcessId) -join ", "
    Write-Error "An Unreal Editor (PID $pids) has $projectName open, or its command line is unreadable. Close it first, or run the script from inside that editor."
}

$log = Join-Path ([IO.Path]::GetTempPath()) ("editor_python_{0:yyyyMMdd_HHmmss}.log" -f (Get-Date))

& $editorCmd $Project -run=pythonscript "-script=$Script" -EnablePlugins=PythonScriptPlugin `
    -unattended -nosplash -nopause -NullRHI -stdout -AllowStdOutLogVerbosity > $log 2>&1

# The commandlet reports "executed successfully" even after an uncaught Python exception, so
# the log is the only reliable signal.
$pythonLines = Select-String -Path $log -Pattern "LogPython:" | Where-Object { $_.Line -notmatch "LogInit:" }
$pythonLines | ForEach-Object { $_.Line -replace "^\[[^\]]*\]\[[^\]]*\]", "" }
Select-String -Path $log -Pattern "^Traceback|^\s+File |^\w+Error:" | ForEach-Object { $_.Line }

$failed = Select-String -Path $log -Pattern "LogPython: Error|^Traceback" -Quiet
Write-Host "Full log: $log"
if ($failed) {
    Write-Host "RESULT: FAILED" -ForegroundColor Red
    exit 1
}
Write-Host "RESULT: OK" -ForegroundColor Green
