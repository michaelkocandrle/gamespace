<#
.SYNOPSIS
    Runs the project's tests with one summary: the offline ones by default, the Blender and Unreal ones on request.

.DESCRIPTION
    Offline (plain Python, seconds; GitHub Actions runs the same command with pwsh on Linux,
    .github/workflows/offline-tests.yml):
      - compileall of Tools/ and Content/Python/ (syntax of every script);
      - the unit tests in Tools/*/tests/ (ship export core, import plan, silhouette compare);
      - the static checks in Tools/Tests/ that need neither Unreal nor Blender (material HLSL, decal orientation,
      the size limit of Docs/CURRENT.md, exterior and interior drawings vs data, the heavy-resource lock, the
      per-checkout build folder).
    -Blender adds the checks that start Blender 5.2 headless (test_ship_geometry.py, the silhouette render).
    -UE adds every Unreal test in Tools/Tests/ (the files that import unreal), one editor commandlet each through
    Tools\run_editor_python.ps1: about a minute per test, the editor must be closed and the C++ built.

    A test fails on a non-zero exit code, a traceback, a "SUMMARY ... FAIL" line or, for Unreal, a missing SUMMARY
    (the test never finished). Every test's output goes to a log; failures print their FAIL lines.
    Python writes its bytecode under %TEMP%\gamespace_pycache, not next to the scripts.

.EXAMPLE
    .\Tools\Test.ps1
.EXAMPLE
    .\Tools\Test.ps1 -UE -Filter *landing*,*vtol*
.EXAMPLE
    .\Tools\Test.ps1 -All
#>
param(
    [switch]$Blender,
    [switch]$UE,
    [switch]$All,
    # wildcards on the file name for the Blender and Unreal tests, e.g. *quantum*,*landing*
    [string[]]$Filter = @("*")
)

# Native tools write to stderr; with "Stop" Windows PowerShell would turn that into a terminating error.
$ErrorActionPreference = "Continue"
if ($All) { $Blender = $true; $UE = $true }
if ($Blender -or $UE) {
    # keep the heavy-resource lock fresh while this runs (author 1. 10. 2026: heartbeat; nothing when this session
    # does not hold the lock - Tools/HeavyLock.ps1 beat)
    try { & (Join-Path $PSScriptRoot "HeavyLock.ps1") beat -OwnerPid $PID } catch { Write-Host "HEAVYLOCK heartbeat not started: $_" }
}
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$logDir = Join-Path $repo ("Saved/Tests/{0:yyyyMMdd_HHmmss}" -f (Get-Date))
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$oldPrefix = $env:PYTHONPYCACHEPREFIX
$oldSkip = $env:GAMESPACE_SKIP_BLENDER
$env:PYTHONPYCACHEPREFIX = Join-Path ([IO.Path]::GetTempPath()) "gamespace_pycache"
if (-not $Blender) { $env:GAMESPACE_SKIP_BLENDER = "1" }

$results = New-Object System.Collections.Generic.List[object]

function Test-Name([string]$Name) {
    foreach ($pattern in $Filter) { if ($Name -like $pattern) { return $true } }
    return $false
}
$runnerError = $null

function Get-Counts([string[]]$Lines) {
    # "IFCSTEST PASS name", "DECALTEST FAIL name", "PASS name" (silhouette), unittest's "Ran 11 tests".
    $pass = @($Lines | Where-Object { $_ -match '(^|\s)([A-Z0-9]+TEST )?PASS\s' -and $_ -notmatch 'SUMMARY' }).Count
    $fail = @($Lines | Where-Object { $_ -match '(^|\s)([A-Z0-9]+TEST )?FAIL\s' -and $_ -notmatch 'SUMMARY' }).Count
    $skip = @($Lines | Where-Object { $_ -match '(^|\s)([A-Z0-9]+TEST )?SKIP\b' }).Count
    $ran = $Lines | Select-String -Pattern '^Ran (\d+) tests?' | Select-Object -First 1
    if ($ran) {
        $total = [int]$ran.Matches[0].Groups[1].Value
        $failed = 0
        foreach ($m in [regex]::Matches(($Lines -join "`n"), '^FAILED \((.*)\)$', 'Multiline')) {
            foreach ($n in [regex]::Matches($m.Groups[1].Value, '(failures|errors)=(\d+)')) { $failed += [int]$n.Groups[2].Value }
        }
        $pass = $total - $failed; $fail = $failed
    }
    return @{ Pass = $pass; Fail = $fail; Skip = $skip }
}

function Add-Result([string]$Group, [string]$Name, [string[]]$Lines, [int]$Code, [double]$Seconds, [switch]$NeedSummary) {
    $Lines = [string[]]@($Lines | Where-Object { $null -ne $_ })   # compileall -q prints nothing
    $log = Join-Path $logDir ("{0}_{1}.log" -f $Group, ($Name -replace '[\\/:]', '_'))
    [IO.File]::WriteAllLines($log, $Lines)
    $counts = Get-Counts $Lines
    $reasons = @()
    if ($Code -ne 0) { $reasons += "exit $Code" }
    if ($Lines -match '^Traceback') { $reasons += "traceback" }
    if ($Lines -match 'SUMMARY\s+(FAIL|FAILED)\b') { $reasons += "summary FAIL" }
    if ($NeedSummary -and -not ($Lines -match 'SUMMARY')) { $reasons += "no SUMMARY (did not finish)" }
    $status = if ($reasons) { "FAIL" } elseif ($counts.Pass -eq 0 -and $counts.Skip -gt 0) { "SKIP" } else { "PASS" }
    $results.Add([pscustomobject]@{ Group = $Group; Name = $Name; Status = $status; Pass = $counts.Pass; Fail = $counts.Fail;
                                    Skip = $counts.Skip; Seconds = [math]::Round($Seconds, 1); Log = $log; Why = ($reasons -join ", ") })
    $color = @{ PASS = "Green"; FAIL = "Red"; SKIP = "Yellow" }[$status]
    Write-Host ("{0,-4}  {1,-8} {2,-38} {3,5} ok {4,3} fail {5,3} skip {6,7:0.0} s  {7}" -f $status, $Group, $Name,
        $counts.Pass, $counts.Fail, $counts.Skip, $Seconds, ($reasons -join ", ")) -ForegroundColor $color
    if ($status -eq "FAIL") {
        $bad = @($Lines | Where-Object { $_ -match '(^|\s)([A-Z0-9]+TEST )?FAIL|^Traceback|Error:|^FAILED|RESULT: FAILED' } |
            Select-Object -First 15)
        $bad | ForEach-Object { Write-Host "        $_" }
        Write-Host "        log: $log"
        if ($env:GITHUB_ACTIONS) {
            # an annotation the public API serves without a login (job logs need admin rights; no gh here)
            $msg = (@("$Name ($($reasons -join ', '))") + $bad + @($Lines | Select-Object -Last 8)) -join '%0A'
            Write-Host "::error title=$Group $Name::$msg"
        }
    }
}

function Invoke-Python([string]$Group, [string]$Name, [string[]]$Arguments) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Push-Location $repo
    try { $lines = & python @Arguments 2>&1 | ForEach-Object { "$_" }; $code = $LASTEXITCODE } finally { Pop-Location }
    Add-Result $Group $Name $lines $code $sw.Elapsed.TotalSeconds
}

try {
    Write-Host "Offline tests (logs in $logDir)"
    Invoke-Python "offline" "compileall Tools Content/Python" @("-m", "compileall", "-q", "Tools", "Content/Python")
    $offline = @(Get-ChildItem (Join-Path $repo "Tools") -Recurse -Filter "test_*.py" |
        Where-Object { $_.Directory.Name -ceq "tests" }) +
        @("test_material_hlsl.py", "test_decal_orientation.py", "test_docs_limits.py", "test_exterior_drawing.py",
          "test_interior_drawing.py", "test_heavy_lock.py", "test_build_dir.py", "test_triangle_budget.py", "test_kit_decals.py" |
          ForEach-Object { Get-Item (Join-Path $repo "Tools/Tests/$_") })
    foreach ($file in $offline) {
        Invoke-Python "offline" $file.Name @($file.FullName)
    }

    if ($Blender) {
        Write-Host "Blender tests"
        foreach ($file in Get-ChildItem (Join-Path $repo "Tools/Tests") -Filter "test_ship_geometry.py" | Where-Object { Test-Name $_.Name }) {
            Invoke-Python "blender" $file.Name @($file.FullName)
        }
    }

    if ($UE) {
        Write-Host "Unreal tests (one editor commandlet each)"
        $ueTests = Get-ChildItem (Join-Path $repo "Tools/Tests") -Filter "test_*.py" |
            Where-Object { (Test-Name $_.Name) -and (Select-String -Path $_.FullName -Pattern '^import unreal' -Quiet) } |
            Sort-Object Name
        foreach ($file in $ueTests) {
            $sw = [Diagnostics.Stopwatch]::StartNew()
            try {
                $lines = & (Join-Path $PSScriptRoot "run_editor_python.ps1") -Script $file.FullName *>&1 | ForEach-Object { "$_" }
                $code = $LASTEXITCODE
            } catch {
                $lines = @("$_"); $code = 1
            }
            Add-Result "ue" $file.Name $lines $code $sw.Elapsed.TotalSeconds -NeedSummary
        }
    }
} catch {
    # A bug in this script must not end in "RESULT: OK" with half the tests unrun.
    $runnerError = "$_"
    Write-Host "RUNNER ERROR: $_" -ForegroundColor Red
} finally {
    $env:PYTHONPYCACHEPREFIX = $oldPrefix
    $env:GAMESPACE_SKIP_BLENDER = $oldSkip
}

$failed = @($results | Where-Object Status -eq "FAIL")
Write-Host ""
Write-Host "===== SUMMARY ====="
foreach ($group in ($results | Select-Object -ExpandProperty Group -Unique)) {
    $in = @($results | Where-Object Group -eq $group)
    Write-Host ("{0,-8} {1} tests: {2} passed, {3} failed, {4} skipped; {5} checks ok, {6} checks failed; {7:0.0} s" -f $group,
        $in.Count, @($in | Where-Object Status -eq "PASS").Count, @($in | Where-Object Status -eq "FAIL").Count,
        @($in | Where-Object Status -eq "SKIP").Count, ($in | Measure-Object Pass -Sum).Sum, ($in | Measure-Object Fail -Sum).Sum,
        ($in | Measure-Object Seconds -Sum).Sum)
}
if ($failed) {
    Write-Host ("RESULT: FAILED - {0}" -f (($failed | ForEach-Object { "$($_.Name) ($($_.Why))" }) -join "; ")) -ForegroundColor Red
    exit 1
}
if ($runnerError -or $results.Count -eq 0) {
    Write-Host "RESULT: FAILED - the runner stopped: $runnerError" -ForegroundColor Red
    exit 1
}
Write-Host "RESULT: OK" -ForegroundColor Green
