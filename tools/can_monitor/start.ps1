param([switch]$Demo)
$ErrorActionPreference='Stop'
$candidates=@((Join-Path $PSScriptRoot '.venv/Scripts/pythonw.exe'), (Join-Path $PSScriptRoot '.venv/bin/pythonw.exe'))
$python=$candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) { throw 'Python environment missing. See README.md for setup.' }
$arguments=@('"'+(Join-Path $PSScriptRoot 'can_monitor.py')+'"')
if ($Demo) { $arguments += '--demo' }
Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $PSScriptRoot -WindowStyle Normal
