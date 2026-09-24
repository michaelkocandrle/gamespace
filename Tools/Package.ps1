<#
.SYNOPSIS
    Builds the standalone Windows game (cooked, Development) into C:\gamespace\Builds\Gamespace.

.DESCRIPTION
    The packaged game runs without the editor: full frame rate, real fullscreen, the same
    shaders and materials the finished game would use. Run it with Tools\Play.ps1.

    The game starts on the title screen (MainMenu). Double-click Windows\gamespace.exe in the
    build folder, or run Tools\Play.ps1. The folder is self-contained: copy it anywhere.

    After packaging the script checks that assets C++ loads by path (sounds, input, materials) made
    it into the build; the cooker only follows references, see DirectoriesToAlwaysCook in
    Config\DefaultGame.ini.

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
    [string]$Config = "Development",
    # Default: <folder above the project>\Builds\Gamespace, i.e. C:\gamespace\Builds\Gamespace
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$Project = (Resolve-Path $Project).Path
$projectDir = Split-Path $Project
$archive = if ($OutputDir) { $OutputDir } else { Join-Path (Split-Path $projectDir) "Builds\Gamespace" }
$uat = Join-Path $EngineDir "Engine\Build\BatchFiles\RunUAT.bat"

$projectName = [IO.Path]::GetFileName($Project)
$openEditors = Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor.exe'" |
    Where-Object { -not $_.CommandLine -or $_.CommandLine -like "*$projectName*" }
if ($openEditors) {
    Write-Error "Close the Unreal Editor first (PID $(($openEditors | ForEach-Object ProcessId) -join ', '))."
}

# A game left running (a shot run that hung) locks gamespace.exe and the archive step fails later.
Get-Process gamespace -ErrorAction SilentlyContinue | Stop-Process -Force

# The local Zen storage server the cook writes to dies now and then; the pak step then fails with
# "Failed reading oplog from Zen" (WORKFLOW.md 9). Start it if it is not there, and on that failure
# restart it and run once more.
$zenLaunch = Join-Path $EngineDir "Engine\Binaries\Win64\ZenLaunch.exe"
function Start-Zen([switch]$Restart) {
    if ($Restart) { Get-Process zenserver -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep 2 }
    if (-not (Get-Process zenserver -ErrorAction SilentlyContinue) -and (Test-Path $zenLaunch)) {
        Start-Process $zenLaunch -WindowStyle Hidden
        Start-Sleep 6
    }
}
Start-Zen

$started = Get-Date
for ($attempt = 1; $attempt -le 2; $attempt++) {
    $output = & $uat BuildCookRun "-project=$Project" -noP4 -platform=Win64 "-clientconfig=$Config" `
        -build -cook -stage -pak -archive "-archivedirectory=$archive" -utf8output -nocompileeditor 2>&1 |
        Tee-Object -Variable lines
    $code = $LASTEXITCODE
    if ($code -eq 0 -or -not ($lines -match "Failed reading oplog from Zen")) { break }
    Write-Host "Zen storage server dropped out; restarting it and packaging once more."
    Start-Zen -Restart
}
$minutes = [math]::Round(((Get-Date) - $started).TotalMinutes, 1)

$exe = Join-Path $archive "Windows\gamespace.exe"
if ($code -ne 0 -or -not (Test-Path $exe)) {
    Write-Host "PACKAGE FAILED (exit $code, $minutes min). The UAT log is under $EngineDir\Engine\Programs\AutomationTool\Saved\Logs."
    exit 1
}
# Assets loaded by path from C++ must be in the build (they were not, before DirectoriesToAlwaysCook).
$manifest = Join-Path $archive "Windows\Manifest_UFSFiles_Win64.txt"
$required = @(
    "Maps/MainMenu.umap", "Maps/TestSpace.umap",
    "Ships/Audio/SW_EngineLoop.uasset", "Ships/Audio/SW_EngineHum.uasset", "Ships/Audio/SW_CruiseCharge.uasset",
    "UI/Audio/SW_MenuAmbience.uasset", "Input/IMC_Spaceship.uasset", "Input/IA_QuantumEngage.uasset",
    "Environments/Space/M_SpaceDust.uasset", "Blueprints/BP_SpaceGameMode.uasset",
    # The HUD's fonts are raw .ttf files staged as UFS (DefaultGame.ini); without them the packaged
    # HUD silently fell back to Roboto (until 19. 9. 2026 the staging path was wrong).
    "UI/Fonts/Rajdhani-Medium.ttf", "UI/Fonts/ShareTechMono-Regular.ttf"
)
if (Test-Path $manifest) {
    $listed = Get-Content $manifest -Raw
    $missing = $required | Where-Object { $listed -notlike "*Content/$_*" }
    if ($missing) {
        Write-Host "PACKAGE INCOMPLETE: not in the build: $($missing -join ', ')"
        exit 1
    }
    Write-Host "Content check OK ($($required.Count) key assets present)"
}
Write-Host "PACKAGE OK ($minutes min): $exe"
Write-Host "Start it with: .\Tools\Play.ps1"
