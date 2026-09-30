<#
.SYNOPSIS
    The lock on heavy resources shared by parallel sessions: Unreal editor, UE tests, packaging, Blender, screenshots.

.DESCRIPTION
    One file outside the repository, C:\gamespace-locks\heavy.lock, holding the session name, the task and the time
    (author 30. 9. 2026). Take it before using a heavy resource and release it right after; when it is taken, do the
    work that needs no heavy resource and try again later. A lock older than 2 hours counts as abandoned and is
    replaced. Acquire exits 0 when the lock is yours, 1 when another session holds it.

.EXAMPLE
    .\Tools\HeavyLock.ps1 -Acquire -Session "second session" -Task "UE tests after FShipFlightModel"
.EXAMPLE
    .\Tools\HeavyLock.ps1 -Release -Session "second session"
.EXAMPLE
    .\Tools\HeavyLock.ps1          # who holds it
#>
param(
    [switch]$Acquire,
    [switch]$Release,
    [string]$Session = "",
    [string]$Task = "",
    [string]$Path = "C:\gamespace-locks\heavy.lock",
    [double]$StaleHours = 2
)

$ErrorActionPreference = "Stop"

function Read-Lock {
    if (-not (Test-Path $Path)) { return $null }
    $info = @{ session = ""; task = ""; time = (Get-Item $Path).LastWriteTime }
    foreach ($line in Get-Content $Path -ErrorAction SilentlyContinue) {
        if ($line -match '^(session|task|time)=(.*)$') { $info[$Matches[1]] = $Matches[2] }
    }
    $parsed = [datetime]::MinValue
    if ($info.time -is [string] -and [datetime]::TryParse($info.time, [ref]$parsed)) { $info.time = $parsed }
    $info.age = (Get-Date) - [datetime]$info.time
    return $info
}

function Show([hashtable]$Lock) {
    "{0} holds it since {1:yyyy-MM-dd HH:mm} ({2:N0} min): {3}" -f $Lock.session, $Lock.time, $Lock.age.TotalMinutes, $Lock.task
}

$lock = Read-Lock

if ($Acquire) {
    if (-not $Session) { Write-Error "-Session is required." }
    if ($lock) {
        if ($lock.session -eq $Session) {
            Remove-Item $Path -Force    # ours: renew the time and task below
        } elseif ($lock.age.TotalHours -ge $StaleHours) {
            Write-Host ("STALE lock replaced: " + (Show $lock))
            Remove-Item $Path -Force
        } else {
            Write-Host ("BUSY: " + (Show $lock))
            exit 1
        }
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $Path) | Out-Null
    try {
        # CreateNew fails if another session created the file in the meantime.
        $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
        $writer = New-Object IO.StreamWriter($stream, (New-Object Text.UTF8Encoding($false)))
        $writer.WriteLine("session=$Session")
        $writer.WriteLine("task=$Task")
        $writer.WriteLine("time=" + (Get-Date).ToString("s"))
        $writer.Dispose()
    } catch [System.IO.IOException] {
        Write-Host ("BUSY: " + (Show (Read-Lock)))
        exit 1
    }
    Write-Host "LOCKED by $Session`: $Task"
    exit 0
}

if ($Release) {
    if (-not $lock) { Write-Host "FREE (nothing to release)"; exit 0 }
    if ($Session -and $lock.session -ne $Session) {
        Write-Host ("NOT RELEASED, not ours: " + (Show $lock))
        exit 1
    }
    Remove-Item $Path -Force
    Write-Host "RELEASED"
    exit 0
}

if ($lock) {
    $stale = if ($lock.age.TotalHours -ge $StaleHours) { " (STALE)" } else { "" }
    Write-Host ((Show $lock) + $stale)
} else {
    Write-Host "FREE"
}
