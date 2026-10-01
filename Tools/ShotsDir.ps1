<#
.SYNOPSIS
    Prints where the screenshots live (Tools\shots_dir.py answers the same for Python).

.DESCRIPTION
    GAMESPACE_SHOTS_DIR when set, else D:\gamespace-shots when drive D exists, else <repo>\Saved\Shots
    (author 1. 10. 2026: the 20 GB of pictures moved off drive C). Files in git name a picture as
    "shots:<set>/<file>".

.EXAMPLE
    $root = & .\Tools\ShotsDir.ps1
#>
if ($env:GAMESPACE_SHOTS_DIR) { return $env:GAMESPACE_SHOTS_DIR }
if (Test-Path "D:\") { return "D:\gamespace-shots" }
return (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path "Saved\Shots")
