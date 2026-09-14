[CmdletBinding()]
param(
    [switch]$RefreshOsm,
    [switch]$ForceTiles
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = 'python' }
$blender = & (Join-Path $repoRoot 'scripts\setup\find_blender.ps1')
$boundary = Join-Path $repoRoot 'data\geographic\bgc-working-boundary.geojson'

$fetchArgs = @('scripts/geography/fetch_osm_map_api.py', '--boundary', $boundary, '--label', 'bgc', '--grid', '4')
if ($RefreshOsm) { $fetchArgs += '--refresh' }
& $python @fetchArgs
if ($LASTEXITCODE -ne 0) { throw "M11 OSM acquisition failed (exit $LASTEXITCODE)" }

$meta = Get-ChildItem (Join-Path $repoRoot 'data\raw\osm\bgc-*.meta.json') | Sort-Object Name -Descending | Select-Object -First 1
if (-not $meta) { throw 'No whole-BGC OSM snapshot was produced' }
$snapshot = $meta.FullName.Replace('.meta.json', '.json')
& $python scripts/geography/normalize_osm.py --snapshot $snapshot --boundary $boundary --output-prefix bgc
if ($LASTEXITCODE -ne 0) { throw "M11 normalization failed (exit $LASTEXITCODE)" }
& $python scripts/geography/build_bgc_tiles.py --tile-size 250
if ($LASTEXITCODE -ne 0) { throw "M11 tile planning failed (exit $LASTEXITCODE)" }

$tileArgs = @('--background', '--factory-startup', '--python', (Join-Path $repoRoot 'blender\scripts\generate_bgc_tiles.py'), '--')
if ($ForceTiles) { $tileArgs += '--force' }
& $blender @tileArgs
if ($LASTEXITCODE -ne 0) { throw "M11 tile generation failed (exit $LASTEXITCODE)" }
& $python scripts/validation/publish_bgc_world.py
if ($LASTEXITCODE -ne 0) { throw "M11 publishing failed (exit $LASTEXITCODE)" }
& $python -m unittest tests.test_m11_whole_bgc
if ($LASTEXITCODE -ne 0) { throw "M11 tests failed (exit $LASTEXITCODE)" }
Push-Location (Join-Path $repoRoot 'web')
try { npm run build; if ($LASTEXITCODE -ne 0) { throw "Web production build failed (exit $LASTEXITCODE)" } }
finally { Pop-Location }
