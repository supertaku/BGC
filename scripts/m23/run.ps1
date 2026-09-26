[CmdletBinding()]
param([switch]$Render)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$python = Join-Path $root '.venv/Scripts/python.exe'
$blender = & (Join-Path $root 'scripts/setup/find_blender.ps1')
Push-Location $root
try {
  & $python scripts/m23/prepare.py
  if ($LASTEXITCODE) { throw 'M23 evidence preparation failed' }
  & $python scripts/m23/build.py
  if ($LASTEXITCODE) { throw 'M23 geometry generation failed' }
  & $blender -b --python scripts/m23/blender_build.py -- --tiles
  if ($LASTEXITCODE) { throw 'M23 tile variants failed' }
  & $python scripts/m23/verify.py
  if ($LASTEXITCODE) { throw 'M23 validation failed' }
  if ($Render) {
    & $blender -b --python scripts/m23/blender_build.py -- --render mind_museum mitsukoshi seasons pse suites shangri acpt sm_aura high_street high_street_central track_30th terra_28th kasalikasan greenway burgos_circle mitsukoshi_ensemble one_bonifacio_ensemble --iteration final
    if ($LASTEXITCODE) { throw 'M23 fixed-camera rendering failed' }
  }
  & $python scripts/m23/report.py
  if ($LASTEXITCODE) { throw 'M23 reporting failed' }
} finally { Pop-Location }
