$ErrorActionPreference = 'Stop'
$aegisRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $aegisRoot
& "$aegisRoot/.venv/Scripts/python.exe" -m aegis.cli serve
