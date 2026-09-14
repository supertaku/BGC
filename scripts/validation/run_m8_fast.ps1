[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $venvPython -PathType Leaf) { $venvPython } else { (Get-Command python -ErrorAction Stop).Source }
$blender = & (Join-Path $repoRoot 'scripts\setup\find_blender.ps1')

& $python (Join-Path $repoRoot 'scripts\reconstruction\validate_package.py') (Join-Path $repoRoot 'data\reconstruction_packages\bgc_building_0014')
if ($LASTEXITCODE -ne 0) { throw 'PACKAGE_ERROR: Central Square validation failed' }
& $python (Join-Path $repoRoot 'scripts\reconstruction\validate_package.py') (Join-Path $repoRoot 'data\reconstruction_packages\synthetic_framework_fixture')
if ($LASTEXITCODE -ne 0) { throw 'PACKAGE_ERROR: synthetic fixture validation failed' }
& $python -m unittest discover -s (Join-Path $repoRoot 'tests')
if ($LASTEXITCODE -ne 0) { throw 'PACKAGE_ERROR: Python tests failed' }
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\buildings\bgc_building_0014\scripts\build.py')
if ($LASTEXITCODE -ne 0) { throw 'BLENDER_ERROR: Central Square clean build failed' }
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\buildings\bgc_building_0014\scripts\validate.py')
if ($LASTEXITCODE -ne 0) { throw 'METADATA_ERROR: Central Square GLB validation failed' }
& $python (Join-Path $repoRoot 'scripts\reconstruction\update_asset_registry.py') bgc_building_0014
if ($LASTEXITCODE -ne 0) { throw 'ASSET_REGISTRY_ERROR: manifest update failed' }
Push-Location (Join-Path $repoRoot 'web')
try {
    & npm.cmd run verify:metadata -- ..\exports\glb\buildings\bgc_building_0014_lod1.glb
    if ($LASTEXITCODE -ne 0) { throw 'METADATA_ERROR: Three.js transport failed' }
} finally { Pop-Location }
Write-Output 'BGC_M8_FAST: PASS'
