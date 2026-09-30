# SessionStart hook (.claude/settings.json): puts Docs/CURRENT.md, the one file of current state, into the context
# of every new session. The order of authority of the documents is in CLAUDE.md.
$root = Split-Path (Split-Path $PSScriptRoot)
$current = Join-Path $root "Docs\CURRENT.md"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
if (Test-Path $current) {
    "Current project state (Docs/CURRENT.md; order of authority in CLAUDE.md):"
    ""
    Get-Content -Raw -Encoding UTF8 $current
} else {
    "Docs/CURRENT.md is missing; see CLAUDE.md."
}
