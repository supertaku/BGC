[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$blender = & (Join-Path $repoRoot 'scripts\setup\find_blender.ps1')

foreach ($script in @('integration_test.py', 'procedural_block_test.py', 'structured_data_test.py')) {
    Write-Output "Running Blender script: $script"
    & $blender --background --factory-startup --python (Join-Path $repoRoot "blender\scripts\$script")
    if ($LASTEXITCODE -ne 0) { throw "Blender failed while running $script (exit $LASTEXITCODE)" }
}

Write-Output 'Validating GLB through Blender import'
& $blender --background --factory-startup --python (Join-Path $repoRoot 'blender\scripts\validate_glb.py')
if ($LASTEXITCODE -ne 0) { throw "GLB validation failed (exit $LASTEXITCODE)" }

& (Join-Path $PSScriptRoot 'check_outputs.ps1')

$viewerModelDir = Join-Path $repoRoot 'web\public\models'
New-Item -ItemType Directory -Force -Path $viewerModelDir | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot 'exports\glb\integration-test.glb') -Destination (Join-Path $viewerModelDir 'integration-test.glb') -Force
Write-Output 'PASS copied GLB into viewer public assets'
