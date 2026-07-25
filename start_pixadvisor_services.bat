@echo off
REM Inicia TODOS los servicios Python de Pixadvisor en ventanas separadas.
REM Doble-click en este archivo cada vez que vayas a trabajar.
REM Para parar: cerrar las ventanas individuales o Ctrl+C en cada una.

setlocal
set "ROOT=%~dp0"

echo.
echo ============================================================
echo   PIXADVISOR LOCAL SERVICES
echo ============================================================
echo   Iniciando servicios Python en ventanas separadas...
echo.

REM 1) GEE Token Proxy (puerto 9101)
if exist "%ROOT%pix-admin\gee-token-proxy.py" (
    start "GEE Token Proxy :9101" cmd /k "cd /d %ROOT%pix-admin && python gee-token-proxy.py"
    echo   [OK] GEE Token Proxy en puerto 9101
)

REM 2) GEE Backend (puerto 9103)
if exist "%ROOT%pix-admin\gee-backend.py" (
    start "GEE Backend :9103" cmd /k "cd /d %ROOT%pix-admin && python gee-backend.py"
    echo   [OK] GEE Backend en puerto 9103
)

REM 3) User API (puerto 9105)
if exist "%ROOT%pix-admin\user-api.py" (
    start "User API :9105" cmd /k "cd /d %ROOT%pix-admin && python user-api.py"
    echo   [OK] User API en puerto 9105
)

REM 4) Field Delineation API (puerto 8765) - cadastro AI de lotes
if exist "%ROOT%POC_FIELD_BOUNDARY\api\main.py" (
    start "Field Delineation API :8765" cmd /k "cd /d %ROOT%POC_FIELD_BOUNDARY\api && python -m uvicorn main:app --host 0.0.0.0 --port 8765"
    echo   [OK] Field Delineation API en puerto 8765
)

REM 5) Pix Admin frontend local (puerto 9100) - sirve los HTML/JS de pix-admin
start "Pix Admin Frontend :9100" cmd /k "cd /d %ROOT% && python -m http.server 9100"
echo   [OK] Pix Admin Frontend en puerto 9100

REM Esperar un poco y abrir el navegador
timeout /t 3 /nobreak >nul
start "" "http://localhost:9100/pix-admin/"

echo.
echo ============================================================
echo   Servicios arrancados.
echo.
echo   Pix Admin (LOCAL, USAR ESTE):
echo     http://localhost:9100/pix-admin/
echo.
echo   Login: pix / admin
echo   Sidebar -^> Cadastro -^> Cadastro AI (NEW)
echo.
echo   La version online (pixadvisor.network) NO tiene los
echo   features Python por restriccion HTTPS-^>HTTP localhost.
echo ============================================================
echo.
echo Esta ventana no necesita quedar abierta. Cerrar con cualquier tecla.
pause >nul
