<#
.SYNOPSIS
    Prints the Unreal Engine 5.8 folder the project's tools use: $env:GAMESPACE_UE_ROOT, or the default install.

.DESCRIPTION
    The one place that names the engine folder (audit v1, 30. 9. 2026). The PowerShell tools take it as the default
    of their -EngineDir; Tools/Assets/install_mannequin_pack.py reads the $default line below. On another machine set
    the variable once:
        [Environment]::SetEnvironmentVariable("GAMESPACE_UE_ROOT", "D:\Epic\UE_5.8", "User")

.EXAMPLE
    & "$(.\Tools\UERoot.ps1)\Engine\Binaries\Win64\UnrealInsights.exe"
#>
$default = "C:\Program Files\Epic Games\UE_5.8"

$root = if ($env:GAMESPACE_UE_ROOT) { $env:GAMESPACE_UE_ROOT.TrimEnd('\', '/') } else { $default }
if (-not (Test-Path (Join-Path $root "Engine\Binaries\Win64"))) {
    Write-Warning "No Unreal Engine at $root (GAMESPACE_UE_ROOT, or the default $default)."
}
$root
