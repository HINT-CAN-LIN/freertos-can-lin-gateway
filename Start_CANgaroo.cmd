@echo off
set "VCU_PROJECT_ROOT=%~dp0"
cd /d "%~dp0"
start "" "%LOCALAPPDATA%\Programs\CANgaroo\0.7.0\cangaroo.exe" "%~dp0tools\cangaroo\VCU_Motor.cangaroo"
