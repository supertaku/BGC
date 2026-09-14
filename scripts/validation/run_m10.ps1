[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $venvPython -PathType Leaf) { $venvPython } else { (Get-Command python -ErrorAction Stop).Source }
$blender = & (Join-Path $repoRoot 'scripts\setup\find_blender.ps1')

& $python (Join-Path $repoRoot 'scripts\reconstruction\build_batch.py') --wave ALL --stage full --continue-on-error
if ($LASTEXITCODE -ne 0) { throw 'M10 full target validation failed' }
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\buildings\bgc_building_0014\scripts\build.py')
if ($LASTEXITCODE -ne 0) { throw 'Central Square regression build failed' }
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\buildings\bgc_building_0007\scripts\build.py')
if ($LASTEXITCODE -ne 0) { throw 'W Global regression build failed' }
& $python (Join-Path $repoRoot 'scripts\reconstruction\build_building.py') --package (Join-Path $repoRoot 'data\reconstruction_packages\synthetic_framework_fixture') --stage full --clean
if ($LASTEXITCODE -ne 0) { throw 'Generic fixture failed' }
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\scripts\generate_bgc_pilot.py')
if ($LASTEXITCODE -ne 0) { throw 'Pilot integration failed' }
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\scripts\validate_glb.py') -- --path (Join-Path $repoRoot 'exports\glb\bgc-pilot-base.glb') --metrics (Join-Path $repoRoot 'exports\glb\bgc-pilot-base.metrics.json')
if ($LASTEXITCODE -ne 0) { throw 'Pilot GLB validation failed' }
& $python (Join-Path $repoRoot 'scripts\validation\update_web_manifest.py')
if ($LASTEXITCODE -ne 0) { throw 'Web manifest update failed' }
Push-Location (Join-Path $repoRoot 'web')
try {
    & npm.cmd run lint
    if ($LASTEXITCODE -ne 0) { throw 'Web lint failed' }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Production build failed' }
} finally { Pop-Location }
Write-Output 'BGC_M10_FULL: PASS (browser benchmark is the explicit post-build stage)'
