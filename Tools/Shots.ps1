<#
.SYNOPSIS
    Takes screenshots of the packaged game from a shot list, so a visual change can be checked
    without anyone playing.

.DESCRIPTION
    Starts C:\gamespace\Builds\Gamespace\Windows\gamespace.exe in a window with a shot list
    (Tools\Shots\<preset>.json). The game loads TestSpace, places the ship for every shot, waits for
    it to settle, saves a picture and quits by itself. The pictures land in
    Saved\Shots\<yyyyMMdd_HHmmss>_<preset>\NN_<name>.png and the script prints their full paths.

    The game window takes the foreground for the few seconds it runs, so do not type meanwhile.

    Saved\ is not in git. -Keep also copies the pictures to Docs\Shots\<preset>\<stamp>\, which is,
    for keeping a visual change in the repository's history.

.PARAMETER Preset
    A file in Tools\Shots without the extension: cockpit, hud, ship.

.PARAMETER List
    An explicit path to a shot list instead of -Preset.

.PARAMETER Package
    Runs Tools\Package.ps1 first (needed after any C++ or content change).

.PARAMETER Editor
    The quick loop without packaging (author 28. 9. 2026): runs the project uncooked (UnrealEditor.exe <uproject>
    -game) with the same shot list. The shot runner holds every picture until shaders and assets have finished
    compiling, so new materials are not caught as the default material; the first run after a material change
    compiles for a while (the log says "SHOTS waiting for ..."). For critic rounds on materials and details; the
    game is packaged once at the end of a step.

.PARAMETER PlayerSettings
    Shoot with the player's own GameUserSettings.ini. By default the pictures and timings are taken at the game's
    default quality (epic, global illumination high, TSR 75 %: USpaceUserSettings, the author's measuring
    standard of 27. 9. 2026): the player's file is set aside
    for the run and put back afterwards, whatever quality was last chosen in the menu.

.EXAMPLE
    .\Tools\Shots.ps1 -Preset cockpit
.EXAMPLE
    .\Tools\Shots.ps1 -Preset hud -Package -Keep
.EXAMPLE
    .\Tools\Shots.ps1 -Last          # just print the newest set of pictures
#>
param(
    [string]$Preset = "cockpit",
    [string]$List = "",
    [switch]$Package,
    [switch]$Keep,
    [switch]$Last,
    [int]$Width = 1600,
    [int]$Height = 900,
    [int]$TimeoutSeconds = 180,
    [switch]$PlayerSettings,
    [switch]$Editor,
    # extra command-line switches for the game, e.g. -GameArgs "-NoMegaLightsPrewarm"
    [string[]]$GameArgs = @()
)

$ErrorActionPreference = "Stop"
$projectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$shotsRoot = Join-Path $projectDir "Saved\Shots"

if ($Last) {
    $newest = Get-ChildItem $shotsRoot -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $newest) { Write-Host "No screenshots yet. Run .\Tools\Shots.ps1 -Preset cockpit"; exit 0 }
    Write-Host "Newest set: $($newest.FullName)"
    Get-ChildItem $newest.FullName -Filter *.png | ForEach-Object { Write-Host "  $($_.FullName)" }
    exit 0
}

if ($List) {
    $listPath = (Resolve-Path $List).Path
    $Preset = [IO.Path]::GetFileNameWithoutExtension($listPath)
} else {
    $listPath = Join-Path $projectDir "Tools\Shots\$Preset.json"
    if (-not (Test-Path $listPath)) {
        Write-Host "No shot list $listPath. Available:"
        Get-ChildItem (Join-Path $projectDir "Tools\Shots") -Filter *.json | ForEach-Object { Write-Host "  $($_.BaseName)" }
        exit 1
    }
}

if ($Package) {
    & (Join-Path $PSScriptRoot "Package.ps1")
    if ($LASTEXITCODE -ne 0) { Write-Error "Packaging failed; not taking screenshots." }
}

if ($Editor) {
    $exe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
    $settings = Join-Path $projectDir "Saved\Config\WindowsEditor\GameUserSettings.ini"
    $TimeoutSeconds = [Math]::Max($TimeoutSeconds, 1200)     # the first run after a change compiles shaders
} else {
    $exe = Join-Path (Split-Path $projectDir) "Builds\Gamespace\Windows\gamespace.exe"
    if (-not (Test-Path $exe)) {
        Write-Error "No packaged game at $exe. Run .\Tools\Package.ps1 (or .\Tools\Shots.ps1 -Package)."
    }
    $settings = Join-Path (Split-Path $exe) "gamespace\Saved\Config\Windows\GameUserSettings.ini"
    # The pictures are of the packaged build, so warn when it is older than the source or the content.
    $packagedAt = (Get-Item $exe).LastWriteTime
    $newer = Get-ChildItem (Join-Path $projectDir "Content"), (Join-Path $projectDir "Source") -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object LastWriteTime -gt $packagedAt | Select-Object -First 1
    if ($newer) {
        Write-Host "WARNING: $($newer.Name) changed after the last package; these pictures show the old build. Use -Package or -Editor." -ForegroundColor Yellow
    }
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $shotsRoot "${stamp}_$Preset"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$gameArgs = @()
if ($Editor) { $gameArgs = @("`"$(Join-Path $projectDir 'gamespace.uproject')`"") }
$gameArgs += @("/Game/Maps/TestSpace", "-windowed", "-ResX=$Width", "-ResY=$Height", "-nosplash", "-unattended",
              "-ShotList=`"$listPath`"", "-ShotOut=`"$outDir`"") + $GameArgs
if ($Editor) { $gameArgs = @($gameArgs[0], $gameArgs[1], "-game") + $gameArgs[2..($gameArgs.Count - 1)] }
Write-Host "Shooting $Preset ($((Get-Content $listPath | ConvertFrom-Json).shots.Count) shots) into $outDir"
# The menu's quality (sg.*) is saved in the build's GameUserSettings.ini; a player's "medium" made one set of kit
# timings 5 ms faster than the next (27. 9. 2026). Measure at the default quality unless -PlayerSettings.
$setAside = "$settings.player"
if (-not $PlayerSettings -and (Test-Path $settings)) {
    Copy-Item $settings $setAside -Force
    # the game's own default (USpaceUserSettings): epic at 75 %, global illumination capped at high (2)
    $groups = "[ScalabilityGroups]`r`nsg.ResolutionQuality=75`r`nsg.GlobalIlluminationQuality=2`r`n" + ((@("ViewDistance",
        "AntiAliasing", "Shadow", "Reflection", "PostProcess", "Texture", "Effects", "Foliage", "Shading", "Landscape") |
        ForEach-Object { "sg.${_}Quality=3" }) -join "`r`n") + "`r`n"
    # every section but [ScalabilityGroups] kept as it is; the groups at the default (epic) after the leading
    # ;METADATA comment
    $head = New-Object System.Collections.Generic.List[string]
    $kept = New-Object System.Collections.Generic.List[string]
    $inGroups = $false
    foreach ($line in [IO.File]::ReadAllLines($setAside)) {
        if ($kept.Count -eq 0 -and $line.StartsWith(";")) { $head.Add($line); continue }
        if ($line.StartsWith("[")) { $inGroups = ($line.Trim() -eq "[ScalabilityGroups]") }
        if (-not $inGroups) { $kept.Add($line) }
    }
    [IO.File]::WriteAllLines($settings, @($head) + @($groups.TrimEnd() -split "`r`n") + @("") + @($kept))
}
try {
    $process = Start-Process -FilePath $exe -ArgumentList $gameArgs -PassThru
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        Write-Host "The game did not quit within $TimeoutSeconds s; stopping it." -ForegroundColor Yellow
        try { $process.Kill() } catch {}
    }
} finally {
    if (Test-Path $setAside) { Move-Item $setAside $settings -Force }
}

$pictures = Get-ChildItem $outDir -Filter *.png | Sort-Object Name
if ($pictures.Count -eq 0) {
    Write-Host "RESULT: FAILED - no pictures. Check the log in Saved\Logs\gamespace.log (search for SHOTS)." -ForegroundColor Red
    exit 1
}
foreach ($picture in $pictures) { Write-Host "  $($picture.FullName)" }
if ($Keep) {
    $keepDir = Join-Path $projectDir "Docs\Shots\$Preset\$stamp"
    New-Item -ItemType Directory -Force -Path $keepDir | Out-Null
    Copy-Item "$outDir\*.png" $keepDir
    Write-Host "Kept for the repository: $keepDir"
}
Write-Host "RESULT: OK - $($pictures.Count) picture(s)" -ForegroundColor Green
