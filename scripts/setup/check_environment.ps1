[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$blender = & (Join-Path $PSScriptRoot 'find_blender.ps1')

Write-Output "cwd=$repoRoot"
Write-Output "os=$([System.Environment]::OSVersion.VersionString)"
Write-Output "git_repo=$([bool](Test-Path -LiteralPath (Join-Path $repoRoot '.git')))"
Write-Output "disk_free_bytes=$((Get-PSDrive -Name ([IO.Path]::GetPathRoot($repoRoot).TrimEnd('\').TrimEnd(':'))).Free)"
Write-Output "blender_executable=$blender"
& $blender --version | Select-Object -First 2
git --version
node --version
npm --version
& $blender --background --factory-startup --python-expr "import bpy, sys; print('BGC_ENV: bpy=' + bpy.app.version_string); print('BGC_ENV: python=' + sys.version.replace(chr(10), ' '))"
