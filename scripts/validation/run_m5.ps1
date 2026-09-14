param(
    [switch]$RefreshReferences
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing .venv Python. Follow README.md setup first."
}

Push-Location $root
try {
    & $python "scripts/entities/resolve_entities.py"
    if ($RefreshReferences) {
        & $python "scripts/entities/enrich_wikidata.py" --refresh
        & $python "scripts/references/discover_commons.py" --refresh --limit-per-entity 3 --max-entities 12
        & $python "scripts/references/enrich_commons.py" --refresh --batch-size 20
    } else {
        & $python "scripts/entities/enrich_wikidata.py"
        & $python "scripts/references/discover_commons.py" --limit-per-entity 3 --max-entities 12
        & $python "scripts/references/enrich_commons.py" --batch-size 20
    }
    & $python "scripts/references/dedupe_references.py"
    & $python "scripts/research/build_observations.py"
    & $python "scripts/references/coverage_report.py"
    & $python "scripts/entities/validate_entities.py"
    & $python "scripts/research/build_m5_reports.py"
    & $python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) {
        throw "M5 validation failed with exit code $LASTEXITCODE"
    }
    Write-Output "BGC_M5: PASS (cached metadata path; no full-resolution downloads)"
}
finally {
    Pop-Location
}

