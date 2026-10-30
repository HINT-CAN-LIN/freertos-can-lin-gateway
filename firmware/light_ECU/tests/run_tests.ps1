param([string]$Compiler = 'gcc')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
foreach ($testName in @('test_light_protocol','test_light_irq','test_light_usb')) {
  $testOutput=Join-Path $PSScriptRoot ($testName+'.exe')
  & $Compiler -std=c11 -Wall -Wextra -Werror "-I$projectRoot/Core/Inc" (Join-Path $PSScriptRoot ($testName+'.c')) -o $testOutput
  if ($LASTEXITCODE -ne 0) { throw "Compile failed: $testName" }
  & $testOutput
  if ($LASTEXITCODE -ne 0) { throw "Test failed: $testName" }
}
