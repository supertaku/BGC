[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$relativeFiles = @(
    'data/geographic/bgc-working-boundary.geojson',
    'data/geographic/pilot-boundary.geojson',
    'data/processed/pilot-buildings.geojson',
    'data/processed/pilot-roads.geojson',
    'data/processed/pilot-paths.geojson',
    'data/processed/pilot-open-spaces.geojson',
    'data/processed/pilot-pois.geojson',
    'data/processed/pilot-road-surfaces.geojson',
    'data/processed/pilot-path-surfaces.geojson',
    'data/processed/pilot-open-space-surfaces.geojson',
    'data/processed/pilot-boundary-local.geojson',
    'data/processed/pilot-data-audit.json',
    'blender/scenes/bgc-pilot-base.blend',
    'blender/renders/pilot/aerial.png',
    'blender/renders/pilot/north-oblique.png',
    'blender/renders/pilot/south-oblique.png',
    'blender/renders/pilot/street-test-01.png',
    'blender/renders/pilot/street-test-02.png',
    'exports/glb/bgc-pilot-base.glb',
    'exports/glb/bgc-pilot-base.metrics.json',
    'web/public/models/bgc-pilot-base.glb',
    'web/public/world/pilot-world.json',
    'references/metadata/wikimedia-pilot.json',
    'references/metadata/mapillary-pilot.json',
    'references/metadata/pilot-reference-coverage.json',
    'data/entities/pilot-entities.json',
    'data/entities/aliases.json',
    'data/entities/wikidata-enrichment.json',
    'data/sources/sources.json',
    'data/references/references.json',
    'data/references/observations.json',
    'data/references/conflicts.json',
    'data/references/coverage.json',
    'data/review/entity-match-review.json',
    'data/review/rights-review.json',
    'data/review/reference-review.json',
    'data/reports/m5-summary.json',
    'data/reconstruction_packages/bgc_building_0014/entity.json',
    'data/reconstruction_packages/bgc_building_0014/geometry.geojson',
    'data/reconstruction_packages/bgc_building_0014/observations.json',
    'data/reconstruction_packages/bgc_building_0014/references.json',
    'data/reconstruction_packages/bgc_building_0014/rights.json',
    'data/reconstruction_packages/bgc_building_0014/coverage.json',
    'data/reconstruction_packages/bgc_building_0014/README.md'
)

$failed = $false
foreach ($relative in $relativeFiles) {
    $path = Join-Path $repoRoot $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Write-Error "Missing output: $relative"
        $failed = $true
        continue
    }
    $length = (Get-Item -LiteralPath $path).Length
    if ($length -le 0) {
        Write-Error "Zero-byte output: $relative"
        $failed = $true
        continue
    }
    Write-Output "PASS $relative ($length bytes)"
}
if ($failed) { exit 1 }
