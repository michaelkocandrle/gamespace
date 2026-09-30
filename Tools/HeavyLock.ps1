<#
.SYNOPSIS
    The lock on the heavy resources that parallel sessions share: Unreal editor, UE tests, packaging, Blender, shots.

.DESCRIPTION
    One file outside the repository, C:\gamespace-locks\heavy.lock, with the session name, the task and the time
    (rules in CLAUDE.md, "Paralelní práce a zámek"). Take it before using a heavy resource and release it when done;
    when another session holds it, do work that needs no heavy resource. A lock older than 2 hours is abandoned and
    "take" takes it over. "take" by the session that already holds the lock refreshes its task and time.

    Exit codes: take 0 = the lock is ours, 1 = held by another session; release 0 = released or free, 1 = not ours.

.EXAMPLE
    .\Tools\HeavyLock.ps1 status
.EXAMPLE
    .\Tools\HeavyLock.ps1 take -Task "Wayfarer exterior shots"
.EXAMPLE
    .\Tools\HeavyLock.ps1 release
#>
param(
    [Parameter(Position = 0)][ValidateSet("status", "take", "release")][string]$Action = "status",
    [string]$Task = "",
    # the checkout folder by default: gamespace (main session) or the worktree's folder
    [string]$Session = (Split-Path -Leaf (Resolve-Path (Join-Path $PSScriptRoot "..")).Path)
)

$lockDir = "C:\gamespace-locks"
$lockFile = Join-Path $lockDir "heavy.lock"
$staleHours = 2
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Read-Lock {
    if (-not (Test-Path $lockFile)) { return $null }
    $info = @{}
    # "key: value" as this script writes it, "key=value" as a session may write it by hand
    foreach ($line in [IO.File]::ReadAllLines($lockFile, $utf8)) {
        if ($line -match '^\s*(\w+)\s*[:=]\s*(.*)$') { $info[$Matches[1]] = $Matches[2].Trim() }
    }
    $time = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse($info["time"], [Globalization.CultureInfo]::InvariantCulture,
                                        [Globalization.DateTimeStyles]::None, [ref]$time)) {
        $time = [DateTimeOffset](Get-Item $lockFile).LastWriteTime
    }
    [pscustomobject]@{ Session = $info["session"]; Task = $info["task"]; Time = $time
                       AgeHours = ([DateTimeOffset]::Now - $time).TotalHours }
}

function Show-Lock($lock) {
    "{0}: '{1}' since {2:yyyy-MM-dd HH:mm} ({3:0.0} h)" -f $lock.Session, $lock.Task, $lock.Time.LocalDateTime, $lock.AgeHours
}

function Write-Lock([System.IO.FileMode]$Mode) {
    $text = "session: $Session`r`ntask: $Task`r`ntime: {0}`r`n" -f [DateTimeOffset]::Now.ToString("o")
    $bytes = $utf8.GetBytes($text)
    # CreateNew fails when another session created the file in the meantime, so two sessions never both win.
    $stream = [IO.File]::Open($lockFile, $Mode, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
}

$lock = Read-Lock
switch ($Action) {
    "status" {
        if ($null -eq $lock) { "HEAVYLOCK FREE" }
        elseif ($lock.AgeHours -ge $staleHours) { "HEAVYLOCK ABANDONED " + (Show-Lock $lock) }
        else { "HEAVYLOCK HELD " + (Show-Lock $lock) }
        exit 0
    }
    "take" {
        if (-not $Task) { Write-Error "take needs -Task (what the heavy resource is for)"; exit 2 }
        New-Item -ItemType Directory -Force -Path $lockDir | Out-Null
        if ($null -ne $lock) {
            if ($lock.Session -eq $Session) {
                Write-Lock ([IO.FileMode]::Create)
                "HEAVYLOCK TAKEN (refreshed) by $Session for '$Task'"
                exit 0
            }
            if ($lock.AgeHours -lt $staleHours) {
                "HEAVYLOCK BUSY " + (Show-Lock $lock) + " - do work without heavy resources and try later"
                exit 1
            }
            "HEAVYLOCK taking over an abandoned lock: " + (Show-Lock $lock)
            Remove-Item -Force $lockFile
        }
        try { Write-Lock ([IO.FileMode]::CreateNew) }
        catch [System.IO.IOException] {
            $other = Read-Lock
            "HEAVYLOCK BUSY " + $(if ($other) { Show-Lock $other } else { "(taken a moment ago)" })
            exit 1
        }
        "HEAVYLOCK TAKEN by $Session for '$Task'"
        exit 0
    }
    "release" {
        if ($null -eq $lock) { "HEAVYLOCK FREE (nothing to release)"; exit 0 }
        if ($lock.Session -ne $Session) { "HEAVYLOCK NOT OURS " + (Show-Lock $lock); exit 1 }
        Remove-Item -Force $lockFile
        "HEAVYLOCK RELEASED by $Session"
        exit 0
    }
}
