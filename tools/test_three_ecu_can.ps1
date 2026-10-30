$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    New-Item -ItemType Directory -Force output/can-integration | Out-Null
    $sources = @(
        'tests/test_three_ecu_can.c',
        'firmware/vcu_ECU/Core/Src/vcu_command_codec.c',
        'firmware/motor_ECU/Core/Src/motor_can.c',
        'firmware/motor_ECU/Core/Src/motor_app.c',
        'firmware/motor_ECU/Core/Src/motor_watchdog.c',
        'firmware/cluster_ECU/Core/Src/cluster_state.c',
        'firmware/cluster_ECU/Core/Src/cluster_state_selftest.c'
    )
    & gcc -std=c11 -Wall -Wextra -Werror `
        -Ifirmware/vcu_ECU/Core/Inc -Ifirmware/motor_ECU/Core/Inc `
        -Ifirmware/cluster_ECU/Core/Inc @sources `
        -o output/can-integration/test_three_ecu_can.exe
    if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
    & ./output/can-integration/test_three_ecu_can.exe
    if ($LASTEXITCODE -ne 0) { throw 'Integration test failed' }
} finally { Pop-Location }
