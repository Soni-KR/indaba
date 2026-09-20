$ErrorActionPreference = 'Stop'
$aegisRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $aegisRoot
$aegisPython = "$aegisRoot/.venv/Scripts/python.exe"
& $aegisPython -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw 'Defense tests failed.' }
& $aegisPython -m aegis.cli evaluate --seeds 0 11 29
if ($LASTEXITCODE -ne 0) { throw 'Static experiment failed.' }
& $aegisPython -m aegis.cli evaluate --variants aegis provenance --seeds 0 11 29 --adaptive
if ($LASTEXITCODE -ne 0) { throw 'Adaptive experiment failed.' }
& $aegisPython -m aegis.stress
if ($LASTEXITCODE -ne 0) { throw 'Stress experiment failed.' }
& $aegisPython scripts/build_demo_plan.py
if ($LASTEXITCODE -ne 0) { throw 'Validated demo selection failed.' }
& $aegisPython scripts/build_report.py
if ($LASTEXITCODE -ne 0) { throw 'Report generation failed.' }
