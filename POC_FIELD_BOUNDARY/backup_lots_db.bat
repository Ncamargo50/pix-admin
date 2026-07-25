@echo off
REM Respaldo de la DB SQLite con timestamp. Doble-click cuando quieras.

setlocal enabledelayedexpansion
set "SRC=%~dp0output\pixadvisor_lots.db"
set "BAK_DIR=%~dp0output\backups"
if not exist "%BAK_DIR%" mkdir "%BAK_DIR%"

if not exist "%SRC%" (
    echo No hay DB en %SRC% - no hay nada que respaldar.
    pause
    exit /b 0
)

for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%a"
set "DEST=%BAK_DIR%\pixadvisor_lots_%TS%.db"
copy "%SRC%" "%DEST%" >nul

if errorlevel 1 (
    echo Error al copiar.
) else (
    echo Backup OK: %DEST%
    REM Mantener solo los ultimos 30 backups
    powershell -NoProfile -Command "Get-ChildItem '%BAK_DIR%\pixadvisor_lots_*.db' | Sort-Object LastWriteTime -Descending | Select-Object -Skip 30 | Remove-Item -Force"
)

pause
