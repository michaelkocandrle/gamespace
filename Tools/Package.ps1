<#
.SYNOPSIS
    Builds a standalone Windows game (cooked, Development) into Saved\Packaged\Windows.

.DESCRIPTION
    The packaged game runs without the editor: full frame rate, real fullscreen, the same
    shaders and materials the finished game would use. Run it with Tools\Play.ps1.

    Close the editor first (cooking loads the same assets). The first run takes long
    (C++ game build, shader compilation for every material); later runs only redo what changed.
    Development config keeps the console (~ key), stat commands and the debug HUD.

.EXAMPLE
    .\Tools\Package.ps1
#>
param(
    [string]$Project = (Join-Path $PSScriptRoot "..\gamespace.uproject"),
    [string]$EngineDir = "C:\Program Files\Epic Games\UE_5.8",
    [ValidateSet("Development", "Shipping")]
    [string]$Config = "Development"
)

$ErrorActionPreference = "Stop"
$Project = (Resolve-Path $Project).Path
$projectDir = Split-Path $Project
$archive = Join-Path $projectDir "Saved\Packaged"
$uat = Join-Path $EngineDir "Engine\Build\BatchFiles\RunUAT.bat"

$projectName = [IO.Path]::GetFileName($Project)
$openEditors = Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor.exe'" |
    Where-Object { -not $_.CommandLine -or $_.CommandLine -like "*$projectName*" }
if ($openEditors) {
    Write-Error "Close the Unreal Editor first (PID $(($openEditors | ForEach-Object ProcessId) -join ', '))."
}

$started = Get-Date
& $uat BuildCookRun "-project=$Project" -noP4 -platform=Win64 "-clientconfig=$Config" `
    -build -cook -stage -pak -archive "-archivedirectory=$archive" -utf8output -nocompileeditor
$code = $LASTEXITCODE
$minutes = [math]::Round(((Get-Date) - $started).TotalMinutes, 1)

$exe = Join-Path $archive "Windows\gamespace.exe"
if ($code -ne 0 -or -not (Test-Path $exe)) {
    Write-Host "PACKAGE FAILED (exit $code, $minutes min). The UAT log is under $EngineDir\Engine\Programs\AutomationTool\Saved\Logs."
    exit 1
}
Write-Host "PACKAGE OK ($minutes min): $exe"
Write-Host "Start it with: .\Tools\Play.ps1"
