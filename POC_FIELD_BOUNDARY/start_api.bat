@echo off
REM Pixadvisor Field Delineation API - script de arranque
REM Doble-click para iniciar el server. Despues abrir http://localhost:8765 en el navegador.

setlocal
set "API_DIR=%~dp0api"
cd /d "%API_DIR%"

REM Verificar que el venv/python tenga las dependencias
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python no esta en el PATH. Instala desde python.org y reintenta.
    pause
    exit /b 1
)

REM Verificar que earth-engine este autenticado
python -c "import ee; ee.Initialize(); print('GEE OK')" 2>nul
if errorlevel 1 (
    echo.
    echo Earth Engine no autenticado. Ejecutar UNA SOLA VEZ:
    echo     earthengine authenticate
    echo.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo  Pixadvisor Field Delineation API
echo ===================================================
echo  URL:   http://localhost:8765
echo  Demo:  http://localhost:8765/  (UI cadastro)
echo  Docs:  http://localhost:8765/docs  (Swagger)
echo  Para parar: Ctrl+C en esta ventana
echo ===================================================
echo.
start "" "http://localhost:8765"
python -m uvicorn main:app --host 0.0.0.0 --port 8765
