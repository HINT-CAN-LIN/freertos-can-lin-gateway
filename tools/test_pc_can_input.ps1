$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    & gcc -std=c11 -Wall -Wextra -Werror -Ifirmware/vcu_ECU/Core/Inc tests/test_pc_can_input.c -o output/can-integration/test_pc_can_input.exe
    if ($LASTEXITCODE -ne 0) { throw 'Firmware host test compilation failed' }
    & ./output/can-integration/test_pc_can_input.exe
    if ($LASTEXITCODE -ne 0) { throw 'Firmware host test failed' }
    $env:TEMP = (Resolve-Path output/can-monitor-temp).Path
    $env:TMP = $env:TEMP
    & ./tools/can_monitor/.venv/bin/python.exe -m unittest discover -s tools/can_monitor -p 'test_*.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'PC Tool test failed' }
} finally { Pop-Location }
