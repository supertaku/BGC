[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = (Get-Command python -ErrorAction Stop).Source
$blender = & (Join-Path $repoRoot 'scripts\setup\find_blender.ps1')

& (Join-Path $repoRoot 'scripts\validation\run_m8_fast.ps1')
if ($LASTEXITCODE -ne 0) { throw 'BGC M8 fast validation failed' }
& $python (Join-Path $repoRoot 'scripts\reconstruction\build_building.py') --package (Join-Path $repoRoot 'data\reconstruction_packages\synthetic_framework_fixture') --stage full --clean
if ($LASTEXITCODE -ne 0) { throw 'Generic dry run failed' }
& $python (Join-Path $repoRoot 'scripts\validation\visual_regression.py') --baseline (Join-Path $repoRoot 'blender\buildings\bgc_building_0014\qa\baseline') --current (Join-Path $repoRoot 'blender\buildings\bgc_building_0014\renders\final') --output (Join-Path $repoRoot 'data\reports\visual-regression\bgc_building_0014')
if ($LASTEXITCODE -ne 0) { throw 'Visual regression failed' }
& $python (Join-Path $repoRoot 'scripts\validation\check_m8_regression.py')
if ($LASTEXITCODE -ne 0) { throw 'Central Square semantic regression failed' }
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\framework\experiments\gpu_instancing.py')
if ($LASTEXITCODE -ne 0) { throw 'GPU instancing experiment failed' }
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\scripts\generate_bgc_pilot.py')
if ($LASTEXITCODE -ne 0) { throw 'Pilot integration generation failed' }
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\scripts\validate_glb.py') -- --path (Join-Path $repoRoot 'exports\glb\bgc-pilot-base.glb') --metrics (Join-Path $repoRoot 'exports\glb\bgc-pilot-base.metrics.json')
if ($LASTEXITCODE -ne 0) { throw 'Pilot GLB validation failed' }
& $python (Join-Path $repoRoot 'scripts\validation\update_web_manifest.py')
if ($LASTEXITCODE -ne 0) { throw 'Viewer publication failed' }
Push-Location (Join-Path $repoRoot 'web')
try {
    & npm.cmd run verify:instancing
    if ($LASTEXITCODE -ne 0) { throw 'Three.js instancing verification failed' }
    & npm.cmd run lint
    if ($LASTEXITCODE -ne 0) { throw 'Viewer lint failed' }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Viewer production build failed' }
} finally { Pop-Location }
Write-Output 'BGC_M8_FULL: PASS (browser benchmark capture remains an explicit post-build stage)'
