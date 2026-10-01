<#
.SYNOPSIS
    Prints the packaged game's folder for this checkout, so two sessions never package over each other.

.DESCRIPTION
    The main checkout (C:\gamespace\gamespace) packages into C:\gamespace\Builds\Gamespace; a worktree named
    gamespace-<name> into C:\gamespace\Builds_<name>\Gamespace (author 1. 10. 2026: both sessions packaged into
    Builds and overwrote each other's game). Tools\Package.ps1, Tools\Shots.ps1 and Tools\Play.ps1 use it.

.EXAMPLE
    $exe = Join-Path (& .\Tools\BuildDir.ps1) "Windows\gamespace.exe"
#>
$checkout = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$name = Split-Path -Leaf $checkout
$parent = Split-Path $checkout
$folder = if ($name -like "gamespace-*") { "Builds_" + $name.Substring("gamespace-".Length) } else { "Builds" }
return (Join-Path (Join-Path $parent $folder) "Gamespace")
