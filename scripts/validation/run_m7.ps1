[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $venvPython -PathType Leaf) { $venvPython } else { (Get-Command python -ErrorAction Stop).Source }
$blender = & (Join-Path $repoRoot 'scripts\setup\find_blender.ps1')

& $python (Join-Path $repoRoot 'scripts\reconstruction\validate_package.py') (Join-Path $repoRoot 'data\reconstruction_packages\bgc_building_0014')
if ($LASTEXITCODE -ne 0) { throw "Central Square package validation failed (exit $LASTEXITCODE)" }

& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\buildings\bgc_building_0014\scripts\build.py')
if ($LASTEXITCODE -ne 0) { throw "Central Square standalone build failed (exit $LASTEXITCODE)" }

& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\buildings\bgc_building_0014\scripts\validate.py')
if ($LASTEXITCODE -ne 0) { throw "Central Square GLB re-import validation failed (exit $LASTEXITCODE)" }

& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\scripts\generate_bgc_pilot.py')
if ($LASTEXITCODE -ne 0) { throw "LOD1 pilot integration generation failed (exit $LASTEXITCODE)" }

& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\scripts\validate_glb.py') -- --path (Join-Path $repoRoot 'exports\glb\bgc-pilot-base.glb') --metrics (Join-Path $repoRoot 'exports\glb\bgc-pilot-base.metrics.json')
if ($LASTEXITCODE -ne 0) { throw "Integrated pilot GLB validation failed (exit $LASTEXITCODE)" }

& $python (Join-Path $repoRoot 'scripts\validation\update_web_manifest.py')
if ($LASTEXITCODE -ne 0) { throw "Viewer publication failed (exit $LASTEXITCODE)" }

Push-Location (Join-Path $repoRoot 'web')
try {
    & npm.cmd run lint
    if ($LASTEXITCODE -ne 0) { throw "Viewer lint failed (exit $LASTEXITCODE)" }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw "Viewer production build failed (exit $LASTEXITCODE)" }
} finally {
    Pop-Location
}

Write-Output 'BGC_M7_PIPELINE: PASS'
