<#
.SYNOPSIS
    Builds the editor target (gamespaceEditor Win64 Development) of the project this Tools folder belongs to.

.DESCRIPTION
    Close the editor first. Live Coding only covers function bodies; new files, UPROPERTY/UFUNCTION and header
    changes need this full build (skill unreal-scripting 1). The game target is built by Tools\Package.ps1.

    The project is the one next to this Tools folder, so a second worktree builds its own copy. The engine folder
    comes from Tools\UERoot.ps1 (GAMESPACE_UE_ROOT).

.EXAMPLE
    .\Tools\Build.ps1
#>
param(
    [string]$Project = (Join-Path $PSScriptRoot "..\gamespace.uproject"),
    [string]$EngineDir = (& (Join-Path $PSScriptRoot "UERoot.ps1")),
    [ValidateSet("Development", "DebugGame")]
    [string]$Config = "Development"
)

$ErrorActionPreference = "Stop"
$Project = (Resolve-Path $Project).Path
$build = Join-Path $EngineDir "Engine\Build\BatchFiles\Build.bat"

$started = Get-Date
& $build gamespaceEditor Win64 $Config "-Project=$Project" -WaitMutex -FromMsBuild
$code = $LASTEXITCODE
$minutes = [math]::Round(((Get-Date) - $started).TotalMinutes, 1)
if ($code -ne 0) {
    Write-Host "BUILD FAILED (exit $code, $minutes min)" -ForegroundColor Red
    exit $code
}
Write-Host "BUILD OK ($minutes min): $Project" -ForegroundColor Green
