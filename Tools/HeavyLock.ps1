<#
.SYNOPSIS
    The lock on the heavy resources that parallel sessions share: Unreal editor, UE tests, packaging, Blender, shots.

.DESCRIPTION
    One file outside the repository, C:\gamespace-locks\heavy.lock (GAMESPACE_HEAVY_LOCK overrides it, for tests),
    with the session name, the task, when it was taken, when it was last refreshed and the process of the operation
    that holds it (rules in CLAUDE.md, "Paralelní práce a zámek").

    - take       before using a heavy resource; "take" by the session that already holds it refreshes it.
    - refresh    the heartbeat: the holder refreshes the lock during a long operation.
    - beat       starts a hidden watcher that refreshes the lock every -Seconds (300) as long as the process
                 -OwnerPid (the caller by default) runs, and records that process in the lock. Package.ps1, Shots.ps1,
                 Build.ps1, run_editor_python.ps1 and Test.ps1 (-UE, -Blender, -All) call it themselves; it does
                 nothing when the session does not hold the lock.
    - run        take, heartbeat, run the -Exec command line, release: for other long commands (Blender from Git
                 Bash). Exits with the command's exit code (1 when the lock is busy).
    - release    when done.
    - release-idle  the hook at the end of every response (.claude/settings.json Stop and SessionEnd): releases the
                 session's lock unless the operation recorded in it still runs. Never fails.
    A lock not refreshed for 20 minutes is abandoned and "take" takes it over (author 1. 10. 2026: a session waited
    8 hours for a lock nobody released).

    Exit codes: take 0 = ours, 1 = held by another session; release 0 = released or free, 1 = not ours;
    refresh 0 = refreshed or taken again, 1 = held by another session.

.EXAMPLE
    .\Tools\HeavyLock.ps1 status
.EXAMPLE
    .\Tools\HeavyLock.ps1 take -Task "Wayfarer exterior shots"
.EXAMPLE
    .\Tools\HeavyLock.ps1 run -Task "Wayfarer rebuild" -Exec "bash -c 'cd ArtSource/Ships/Wayfarer && ...'"
.EXAMPLE
    .\Tools\HeavyLock.ps1 release
#>
param(
    [Parameter(Position = 0)][ValidateSet("status", "take", "refresh", "beat", "watch", "release", "release-idle", "run")]
    [string]$Action = "status",
    [string]$Task = "",
    # the checkout folder by default: gamespace (main session) or the worktree's folder
    [string]$Session = "",
    [int]$OwnerPid = 0,
    [int]$Seconds = 300,
    [string]$LockFile = "",
    # run: the command line to run under the lock (PowerShell syntax, e.g. "bash -c '...'")
    [string]$Exec = ""
)

# (not in the param defaults: Windows PowerShell leaves $PSScriptRoot empty there under -File)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Session) { $Session = Split-Path -Leaf (Resolve-Path (Join-Path $here "..")).Path }

if (-not $LockFile) {
    $LockFile = if ($env:GAMESPACE_HEAVY_LOCK) { $env:GAMESPACE_HEAVY_LOCK } else { "C:\gamespace-locks\heavy.lock" }
}
$staleMinutes = 20
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Parse-Time([string]$text) {
    $t = [DateTimeOffset]::MinValue
    if ($text -and [DateTimeOffset]::TryParse($text, [Globalization.CultureInfo]::InvariantCulture,
                                               [Globalization.DateTimeStyles]::None, [ref]$t)) { return $t }
    return $null
}

function Read-Lock {
    if (-not (Test-Path -LiteralPath $LockFile)) { return $null }
    $info = @{}
    # "key: value" as this script writes it, "key=value" as a session may write it by hand
    try { $lines = [IO.File]::ReadAllLines($LockFile, $utf8) } catch { return $null }
    foreach ($line in $lines) {
        if ($line -match '^\s*(\w+)\s*[:=]\s*(.*)$') { $info[$Matches[1]] = $Matches[2].Trim() }
    }
    $taken = Parse-Time $info["time"]
    if ($null -eq $taken) { $taken = [DateTimeOffset](Get-Item -LiteralPath $LockFile).LastWriteTime }
    $refreshed = Parse-Time $info["refreshed"]
    if ($null -eq $refreshed) { $refreshed = $taken }
    $procId = 0
    [void][int]::TryParse("" + $info["pid"], [ref]$procId)
    $watcher = 0
    [void][int]::TryParse("" + $info["watcher"], [ref]$watcher)
    [pscustomobject]@{ Session = $info["session"]; Task = $info["task"]; Time = $taken; Refreshed = $refreshed
                       Pid = $procId; Watcher = $watcher
                       IdleMinutes = ([DateTimeOffset]::Now - $refreshed).TotalMinutes }
}

function Alive([int]$id) {
    if ($id -le 0) { return $false }
    return $null -ne (Get-Process -Id $id -ErrorAction SilentlyContinue)
}

function Show-Lock($lock) {
    $op = if ($lock.Pid -gt 0) { if (Alive $lock.Pid) { ", operation pid {0} running" -f $lock.Pid } else { ", operation pid {0} ended" -f $lock.Pid } } else { "" }
    "{0}: '{1}' taken {2:yyyy-MM-dd HH:mm}, refreshed {3:0} min ago{4}" -f $lock.Session, $lock.Task, $lock.Time.LocalDateTime,
        $lock.IdleMinutes, $op
}

function Write-Lock([System.IO.FileMode]$Mode, [string]$taskText, [DateTimeOffset]$taken, [int]$procId, [int]$watcher) {
    $now = [DateTimeOffset]::Now.ToString("o")
    $text = "session: $Session`r`ntask: $taskText`r`ntime: {0}`r`nrefreshed: {1}`r`npid: {2}`r`nwatcher: {3}`r`n" -f `
        $taken.ToString("o"), $now, $procId, $watcher
    $bytes = $utf8.GetBytes($text)
    # CreateNew fails when another session created the file in the meantime, so two sessions never both win.
    $stream = [IO.File]::Open($LockFile, $Mode, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
}

function Take([string]$taskText, [int]$procId) {
    $dir = Split-Path -Parent $LockFile
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $lock = Read-Lock
    if ($null -ne $lock) {
        if ($lock.Session -eq $Session) {
            Write-Lock ([IO.FileMode]::Create) $taskText $lock.Time $procId $lock.Watcher
            Write-Host ("HEAVYLOCK TAKEN (refreshed) by $Session for '$taskText'")
            return $true
        }
        if ($lock.IdleMinutes -lt $staleMinutes) {
            Write-Host ("HEAVYLOCK BUSY " + (Show-Lock $lock) + " - do work without heavy resources and try later")
            return $false
        }
        Write-Host ("HEAVYLOCK taking over an abandoned lock (no refresh for $staleMinutes min): " + (Show-Lock $lock))
        Remove-Item -Force -LiteralPath $LockFile
    }
    try { Write-Lock ([IO.FileMode]::CreateNew) $taskText ([DateTimeOffset]::Now) $procId 0 }
    catch [System.IO.IOException] {
        $other = Read-Lock
        Write-Host ("HEAVYLOCK BUSY " + $(if ($other) { Show-Lock $other } else { "(taken a moment ago)" }))
        return $false
    }
    Write-Host ("HEAVYLOCK TAKEN by $Session for '$taskText'")
    return $true
}

function Start-Watcher([int]$owner) {
    $exe = (Get-Process -Id $PID).Path
    $argv = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PSCommandPath, "watch", "-OwnerPid", $owner,
              "-Seconds", $Seconds, "-Session", $Session, "-LockFile", $LockFile) |
        ForEach-Object { if ("$_" -match '\s') { '"' + $_ + '"' } else { "$_" } }
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        $p = Start-Process -FilePath $exe -ArgumentList $argv -WindowStyle Hidden -PassThru
    } else {
        $p = Start-Process -FilePath $exe -ArgumentList $argv -PassThru
    }
    return $p.Id
}

function Beat([int]$owner) {
    $lock = Read-Lock
    if ($null -eq $lock -or $lock.Session -ne $Session) {
        Write-Host ("HEAVYLOCK no heartbeat: the lock is not held by $Session" + $(if ($lock) { " (" + (Show-Lock $lock) + ")" } else { "" }))
        return
    }
    $watcher = $lock.Watcher
    if (-not (Alive $watcher) -or $lock.Pid -ne $owner) { $watcher = Start-Watcher $owner }
    Write-Lock ([IO.FileMode]::Create) $lock.Task $lock.Time $owner $watcher
    Write-Host "HEAVYLOCK heartbeat every $Seconds s while pid $owner runs (watcher $watcher)"
}

switch ($Action) {
    "status" {
        $lock = Read-Lock
        if ($null -eq $lock) { "HEAVYLOCK FREE" }
        elseif ($lock.IdleMinutes -ge $staleMinutes) { "HEAVYLOCK ABANDONED " + (Show-Lock $lock) }
        else { "HEAVYLOCK HELD " + (Show-Lock $lock) }
        exit 0
    }
    "take" {
        if (-not $Task) { Write-Error "take needs -Task (what the heavy resource is for)"; exit 2 }
        if (Take $Task $OwnerPid) { exit 0 } else { exit 1 }
    }
    "refresh" {
        $lock = Read-Lock
        if ($null -ne $lock -and $lock.Session -eq $Session) {
            $procId = if ($OwnerPid -gt 0) { $OwnerPid } else { $lock.Pid }
            Write-Lock ([IO.FileMode]::Create) $lock.Task $lock.Time $procId $lock.Watcher
            "HEAVYLOCK REFRESHED by $Session"
            exit 0
        }
        if ($null -ne $lock -and $lock.IdleMinutes -lt $staleMinutes) { "HEAVYLOCK LOST " + (Show-Lock $lock); exit 1 }
        if (Take $(if ($Task) { $Task } else { "(taken again by its heartbeat)" }) $OwnerPid) { exit 0 } else { exit 1 }
    }
    "beat" {
        Beat $(if ($OwnerPid -gt 0) { $OwnerPid } else { $PID })
        exit 0
    }
    "watch" {
        # the hidden watcher: refresh while the owner runs and the lock is still ours, then quit
        while (Alive $OwnerPid) {
            $slept = 0
            while ($slept -lt $Seconds -and (Alive $OwnerPid)) { Start-Sleep -Seconds 1; $slept += 1 }
            if (-not (Alive $OwnerPid)) { break }
            $lock = Read-Lock
            if ($null -eq $lock -or $lock.Session -ne $Session) { break }
            Write-Lock ([IO.FileMode]::Create) $lock.Task $lock.Time $lock.Pid $lock.Watcher
        }
        exit 0
    }
    "release" {
        $lock = Read-Lock
        if ($null -eq $lock) { "HEAVYLOCK FREE (nothing to release)"; exit 0 }
        if ($lock.Session -ne $Session) { "HEAVYLOCK NOT OURS " + (Show-Lock $lock); exit 1 }
        Remove-Item -Force -LiteralPath $LockFile
        "HEAVYLOCK RELEASED by $Session"
        exit 0
    }
    "release-idle" {
        try {
            $lock = Read-Lock
            if ($null -ne $lock -and $lock.Session -eq $Session) {
                if (Alive $lock.Pid) { "HEAVYLOCK KEPT: operation pid {0} of {1} still runs" -f $lock.Pid, $Session }
                else { Remove-Item -Force -LiteralPath $LockFile; "HEAVYLOCK RELEASED by $Session (end of response)" }
            }
        } catch { "HEAVYLOCK release-idle: $($_.Exception.Message)" }
        exit 0
    }
    "run" {
        if (-not $Task -or -not $Exec) { Write-Error "run needs -Task and -Exec"; exit 2 }
        if (-not (Take $Task $PID)) { exit 1 }
        Beat $PID
        $code = 0
        try {
            $global:LASTEXITCODE = 0
            Invoke-Expression $Exec
            $code = $LASTEXITCODE
            if ($null -eq $code) { $code = 0 }
        } finally {
            $lock = Read-Lock
            if ($null -ne $lock -and $lock.Session -eq $Session) { Remove-Item -Force -LiteralPath $LockFile }
            "HEAVYLOCK RELEASED by $Session after '$Task' (exit $code)"
        }
        exit $code
    }
}
