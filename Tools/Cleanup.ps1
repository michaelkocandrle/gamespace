<#
.SYNOPSIS
    Keeps drive C from filling up again (author 1. 10. 2026): old shot sets, staging copies, old logs, LFS objects
    that are safely on the remote. Prints what it frees and warns under 30 GB free.

.DESCRIPTION
    Only what can be made again or is not needed:
      - shot sets (Tools\ShotsDir.ps1, D:\gamespace-shots) older than -Days that no file in Docs, Tools or .claude names
        (reviews name them as shots:<set>/...);
      - Saved\StagedBuilds of this checkout (UAT's staging copy; the archived game stays, Tools\BuildDir.ps1);
      - logs, crash reports and test logs older than -Days (Saved\Logs, Saved\Crashes, Saved\Tests, the packaged
        game's Saved\Logs);
      - git lfs prune --verify-remote --verify-unreachable --when-unverified=continue: only LFS objects the remote is
        verified to hold; objects no commit names and the remote lacks are kept (author: only after the second
        session is merged, and on request).
    Never: the archived game, Intermediate, the DDC, ArtSource, anything in another worktree, uncommitted work.

.EXAMPLE
    .\Tools\Cleanup.ps1 -DryRun
.EXAMPLE
    .\Tools\Cleanup.ps1               # at the end of a step, after the push
#>
param(
    [int]$Days = 7,
    [switch]$DryRun,
    [switch]$SkipLfs,
    [double]$WarnBelowGB = 30
)
$ErrorActionPreference = "Continue"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$cut = (Get-Date).AddDays(-$Days)
$script:freed = 0

function Get-Bytes([string]$path) {
    (Get-ChildItem -LiteralPath $path -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum + 0
}
function Remove-Path([string]$path, [string]$why) {
    if (-not (Test-Path -LiteralPath $path)) { return }
    $item = Get-Item -LiteralPath $path -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { Write-Host "  skip link $path"; return }
    $bytes = if ($item.PSIsContainer) { Get-Bytes $path } else { $item.Length }
    if (-not $DryRun) { Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue }
    $script:freed += $bytes
    "{0,9:N1} MB  {1}  ({2})" -f ($bytes / 1MB), $path, $why
}

# 1. shot sets nobody names
$shots = & (Join-Path $PSScriptRoot "ShotsDir.ps1")
$named = Get-ChildItem (Join-Path $repo "Docs"), (Join-Path $repo "Tools"), (Join-Path $repo ".claude") -Recurse -File `
    -Include *.json, *.md, *.py, *.ps1 -ErrorAction SilentlyContinue |
    Select-String -Pattern '(\d{8}_\d{6}_[A-Za-z0-9_]+)' -AllMatches |
    ForEach-Object { $_.Matches | ForEach-Object { $_.Groups[1].Value } } | Sort-Object -Unique
$old = @(Get-ChildItem $shots -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^\d{8}_\d{6}_' -and $_.LastWriteTime -lt $cut -and ($named -notcontains $_.Name) })
$sum = 0
foreach ($s in $old) { $b = Get-Bytes $s.FullName; $sum += $b; if (-not $DryRun) { Remove-Item -LiteralPath $s.FullName -Recurse -Force } }
$script:freed += $sum
"{0,9:N1} MB  {1} shot sets older than {2} days, not named in Docs/Tools/.claude ({3})" -f ($sum / 1MB), $old.Count, $Days, $shots

# 2. UAT's staging copy (the archive in Tools\BuildDir.ps1 is the game)
Remove-Path (Join-Path $repo "Saved\StagedBuilds") "staging copy of the last package"

# 3. old logs and crash reports
$build = & (Join-Path $PSScriptRoot "BuildDir.ps1")
foreach ($dir in (Join-Path $repo "Saved\Logs"), (Join-Path $repo "Saved\Crashes"), (Join-Path $repo "Saved\Tests"),
                 (Join-Path $build "Windows\gamespace\Saved\Logs"), (Join-Path $build "Windows\gamespace\Saved\Crashes")) {
    if (-not (Test-Path $dir)) { continue }
    $items = @(Get-ChildItem $dir -Force -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cut })
    $sum = 0
    foreach ($i in $items) {
        $b = if ($i.PSIsContainer) { Get-Bytes $i.FullName } else { $i.Length }; $sum += $b
        if (-not $DryRun) { Remove-Item -LiteralPath $i.FullName -Recurse -Force -ErrorAction SilentlyContinue }
    }
    $script:freed += $sum
    if ($items.Count) { "{0,9:N1} MB  {1} old items in {2}" -f ($sum / 1MB), $items.Count, $dir }
}

# 4. LFS objects the remote is verified to hold
if (-not $SkipLfs) {
    $lfsArgs = @("lfs", "prune", "--verify-remote", "--verify-unreachable", "--when-unverified=continue")
    if ($DryRun) { $lfsArgs += "--dry-run" }
    $before = (Get-PSDrive C).Free
    $out = & git -C $repo @lfsArgs 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s\*\s[0-9a-f]{64}$' }
    $out | Where-Object { $_ -match 'local objects|pruned|Deleting' } | ForEach-Object { "            git lfs: $_" }
    if (-not $DryRun) { $script:freed += [math]::Max(0, (Get-PSDrive C).Free - $before) }
}

$free = (Get-PSDrive C).Free / 1GB
"CLEANUP {0}: freed {1:N2} GB, C: {2:N1} GB free" -f $(if ($DryRun) { "DRY RUN" } else { "OK" }), ($script:freed / 1GB), $free
if ($free -lt $WarnBelowGB) {
    Write-Host ("WARNING: only {0:N1} GB free on C (under {1} GB). See CURRENT.md for what else can go (Zen DDC to D:)." -f $free, $WarnBelowGB) -ForegroundColor Yellow
}
