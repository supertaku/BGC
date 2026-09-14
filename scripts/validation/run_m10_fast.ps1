[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $venvPython -PathType Leaf) { $venvPython } else { (Get-Command python -ErrorAction Stop).Source }

& $python (Join-Path $repoRoot 'scripts\reconstruction\build_batch.py') --wave ALL --stage build --continue-on-error
if ($LASTEXITCODE -ne 0) { throw 'M10 batch build/GLB validation failed' }
& $python -m unittest discover -s (Join-Path $repoRoot 'tests')
if ($LASTEXITCODE -ne 0) { throw 'M10 Python tests failed' }
Push-Location (Join-Path $repoRoot 'web')
try {
    $batch = Get-Content -Raw (Join-Path $repoRoot 'data\batches\m10-batch.json') | ConvertFrom-Json
    foreach ($target in $batch.targets) {
        & npm.cmd run verify:metadata -- (Join-Path $repoRoot "exports\glb\buildings\$($target.entity_id)_lod1.glb")
        if ($LASTEXITCODE -ne 0) { throw "Metadata validation failed for $($target.entity_id)" }
    }
} finally { Pop-Location }
Write-Output 'BGC_M10_FAST: PASS'
