[CmdletBinding()]
param(
    [switch]$RefreshOsm,
    [switch]$RefreshReferences
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $venvPython -PathType Leaf) { $venvPython } else { (Get-Command python -ErrorAction Stop).Source }

& $python -c 'import pyproj, shapely'
if ($LASTEXITCODE -ne 0) { throw 'Install requirements-geospatial.txt before running the grounded pilot pipeline.' }

$fetchArgs = @((Join-Path $repoRoot 'scripts\geography\fetch_osm.py'))
if ($RefreshOsm) { $fetchArgs += '--refresh' }
& $python @fetchArgs
if ($LASTEXITCODE -ne 0) { throw "OSM fetch/cache validation failed (exit $LASTEXITCODE)" }

& $python (Join-Path $repoRoot 'scripts\geography\normalize_osm.py')
if ($LASTEXITCODE -ne 0) { throw "OSM normalization failed (exit $LASTEXITCODE)" }

& $python (Join-Path $repoRoot 'scripts\validation\test_coordinates.py')
if ($LASTEXITCODE -ne 0) { throw "Coordinate validation failed (exit $LASTEXITCODE)" }
& $python (Join-Path $repoRoot 'scripts\validation\test_processed_data.py')
if ($LASTEXITCODE -ne 0) { throw "Processed-data validation failed (exit $LASTEXITCODE)" }

$commonsArgs = @((Join-Path $repoRoot 'scripts\references\discover_wikimedia.py'))
$mapillaryArgs = @((Join-Path $repoRoot 'scripts\references\discover_mapillary.py'))
if ($RefreshReferences) {
    $commonsArgs += '--refresh'
    $mapillaryArgs += '--refresh'
}
& $python @commonsArgs
if ($LASTEXITCODE -ne 0) { throw "Wikimedia discovery failed (exit $LASTEXITCODE)" }
& $python @mapillaryArgs
if ($LASTEXITCODE -ne 0) { throw "Mapillary integration-boundary check failed (exit $LASTEXITCODE)" }

$blender = & (Join-Path $repoRoot 'scripts\setup\find_blender.ps1')
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\scripts\generate_bgc_pilot.py')
if ($LASTEXITCODE -ne 0) { throw "Pilot Blender generation failed (exit $LASTEXITCODE)" }

$glb = Join-Path $repoRoot 'exports\glb\bgc-pilot-base.glb'
$metrics = Join-Path $repoRoot 'exports\glb\bgc-pilot-base.metrics.json'
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\scripts\validate_glb.py') -- --path $glb --metrics $metrics
if ($LASTEXITCODE -ne 0) { throw "Pilot GLB validation failed (exit $LASTEXITCODE)" }

& $python (Join-Path $repoRoot 'scripts\validation\update_web_manifest.py')
if ($LASTEXITCODE -ne 0) { throw "Viewer asset publication failed (exit $LASTEXITCODE)" }

Write-Output 'BGC_GROUNDED_PILOT_PIPELINE: PASS'
