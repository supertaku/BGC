[CmdletBinding()]
param()

$pathCommand = Get-Command blender -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pathCommand) {
    $pathCommand.Source
    exit 0
}

$candidates = @()
if ($env:ProgramFiles) {
    $candidates += Get-ChildItem -LiteralPath (Join-Path $env:ProgramFiles 'Blender Foundation') -Filter blender.exe -File -Recurse -ErrorAction SilentlyContinue
}
if ($env:LOCALAPPDATA) {
    $candidates += Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'Programs') -Filter blender.exe -File -Recurse -ErrorAction SilentlyContinue
}

$resolved = $candidates | Sort-Object FullName -Descending | Select-Object -First 1
if (-not $resolved) {
    Write-Error 'Blender was not found on PATH or in standard Windows installation directories.'
    exit 1
}

$resolved.FullName
