param([string]$Serial = '066EFF505487525067173344')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$firmware = Join-Path $root 'output/can-integration/vcu-can-input.elf'
if (!(Test-Path -LiteralPath $firmware)) { throw "Firmware missing: $firmware" }
$cli = Get-ChildItem 'C:/ST' -Recurse -Filter STM32_Programmer_CLI.exe | Select-Object -First 1
if (!$cli) { throw 'STM32CubeProgrammer CLI not found under C:/ST' }
# Serial selects only the previously identified VCU, never the Motor board.
& $cli.FullName -c port=SWD "sn=$Serial" mode=UR -d $firmware -v -rst
if ($LASTEXITCODE -ne 0) { throw 'VCU programming/verification failed' }
