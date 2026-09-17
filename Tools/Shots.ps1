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
    [int]$TimeoutSeconds = 180
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

$exe = Join-Path (Split-Path $projectDir) "Builds\Gamespace\Windows\gamespace.exe"
if (-not (Test-Path $exe)) {
    Write-Error "No packaged game at $exe. Run .\Tools\Package.ps1 (or .\Tools\Shots.ps1 -Package)."
}
# The pictures are of the packaged build, so warn when it is older than the source or the content.
$packagedAt = (Get-Item $exe).LastWriteTime
$newer = Get-ChildItem (Join-Path $projectDir "Content"), (Join-Path $projectDir "Source") -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object LastWriteTime -gt $packagedAt | Select-Object -First 1
if ($newer) {
    Write-Host "WARNING: $($newer.Name) changed after the last package; these pictures show the old build. Use -Package." -ForegroundColor Yellow
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $shotsRoot "${stamp}_$Preset"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$gameArgs = @("/Game/Maps/TestSpace", "-windowed", "-ResX=$Width", "-ResY=$Height", "-nosplash", "-unattended",
              "-ShotList=`"$listPath`"", "-ShotOut=`"$outDir`"")
Write-Host "Shooting $Preset ($((Get-Content $listPath | ConvertFrom-Json).shots.Count) shots) into $outDir"
$process = Start-Process -FilePath $exe -ArgumentList $gameArgs -PassThru
if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
    Write-Host "The game did not quit within $TimeoutSeconds s; stopping it." -ForegroundColor Yellow
    try { $process.Kill() } catch {}
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
