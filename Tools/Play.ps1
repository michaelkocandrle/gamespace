<#
.SYNOPSIS
    Starts gamespace fullscreen, outside the editor window.

.DESCRIPTION
    Default: the packaged game from Tools\Package.ps1 (C:\gamespace\Builds\Gamespace\Windows\gamespace.exe),
    with the window mode and resolution from its own settings - the same as double-clicking the exe. That is the closest to the real game:
    no editor overhead, cooked shaders, all materials.

    -Editor runs the project uncooked in game mode (UnrealEditor.exe -game) instead. No packaging
    needed, but it loads slower, and materials created since the editor last compiled their
    shaders can show up as the grey default until the editor has been opened once.

    In the game:
      Escape     pause menu (Resume, Settings, Main menu, Quit); F10 does the same
      H          HUD: compact -> full -> hidden
      ~          console (Development builds): stat fps, stat unit, t.MaxFPS 0, r.ScreenPercentage 100
      Alt+Enter  fullscreen <-> window
      Alt+F4     quit

.EXAMPLE
    .\Tools\Play.ps1
.EXAMPLE
    .\Tools\Play.ps1 -Windowed -Width 1600 -Height 900
.EXAMPLE
    .\Tools\Play.ps1 -Editor
#>
param(
    [switch]$Editor,
    [switch]$Windowed,
    # Exclusive fullscreen instead of borderless: can be a few percent faster, alt-tab is slower.
    [switch]$Exclusive,
    [int]$Width = 0,
    [int]$Height = 0,
    [string]$Project = (Join-Path $PSScriptRoot "..\gamespace.uproject"),
    [string]$EngineDir = "C:\Program Files\Epic Games\UE_5.8",
    # Extra arguments for the game, e.g. '-ExecCmds="stat fps"'
    [string]$Extra = ""
)

$ErrorActionPreference = "Stop"
$Project = (Resolve-Path $Project).Path
$projectDir = Split-Path $Project

$gameArgs = @("-nosplash")
# Without size or mode switches the game uses its own settings (Escape > Settings; the first
# start is borderless fullscreen). With them, this launch overrides the settings.
if ($Windowed -or $Exclusive -or $Width -gt 0 -or $Height -gt 0) {
    if ($Width -le 0 -or $Height -le 0) {
        # Physical pixels (Win32_VideoController ignores Windows display scaling, unlike Forms.Screen).
        $video = Get-CimInstance Win32_VideoController | Where-Object CurrentHorizontalResolution | Select-Object -First 1
        if ($video) {
            $Width = [int]$video.CurrentHorizontalResolution
            $Height = [int]$video.CurrentVerticalResolution
        } else {
            $Width = 1920; $Height = 1080
        }
    }
    # -Res=WxH plus f (fullscreen), wf (borderless fullscreen) or w (window).
    $suffix = if ($Windowed) { "w" } elseif ($Exclusive) { "f" } else { "wf" }
    $gameArgs += "-Res=${Width}x${Height}$suffix"
}
if ($Extra) { $gameArgs += $Extra }

if ($Editor) {
    $exe = Join-Path $EngineDir "Engine\Binaries\Win64\UnrealEditor.exe"
    $gameArgs = @("`"$Project`"", "/Game/Maps/TestSpace", "-game") + $gameArgs
} else {
    $exe = Join-Path (Split-Path $projectDir) "Builds\Gamespace\Windows\gamespace.exe"
    if (-not (Test-Path $exe)) {
        Write-Host "No packaged game at $exe."
        Write-Host "Build it once with .\Tools\Package.ps1 (editor closed), or start uncooked with .\Tools\Play.ps1 -Editor"
        exit 1
    }
    $packagedAt = (Get-Item $exe).LastWriteTime
    $newerContent = Get-ChildItem (Join-Path $projectDir "Content") -Recurse -File |
        Where-Object LastWriteTime -gt $packagedAt | Select-Object -First 1
    if ($newerContent) {
        Write-Host "Note: Content changed after the last package ($($newerContent.Name)); run .\Tools\Package.ps1 to see it."
    }
}

Write-Host "Starting $exe $($gameArgs -join ' ')"
Start-Process -FilePath $exe -ArgumentList $gameArgs
