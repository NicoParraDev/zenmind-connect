@echo off
echo ========================================
echo   INICIANDO SERVIDOR CON ACCESO A RED
echo ========================================
echo.

REM Verificar que .env existe
if not exist .env (
    echo ERROR: No se encontro el archivo .env
    echo Por favor crea el archivo .env primero
    pause
    exit /b 1
)

REM Verificar ALLOWED_HOSTS
findstr /C:"192.168.1.83" .env >nul
if %errorlevel% neq 0 (
    echo Actualizando ALLOWED_HOSTS en .env...
    powershell -Command "(Get-Content .env) -replace 'ALLOWED_HOSTS=localhost,127.0.0.1', 'ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83' | Set-Content .env"
    echo ✓ ALLOWED_HOSTS actualizado
) else (
    echo ✓ ALLOWED_HOSTS ya esta configurado correctamente
)

echo.
echo ========================================
echo   SERVIDOR INICIANDO...
echo ========================================
echo.
echo El servidor estara disponible en:
echo   - Local: http://127.0.0.1:8000
echo   - Red local: http://192.168.1.83:8000
echo.
echo Desde otro dispositivo en la misma red WiFi:
echo   http://192.168.1.83:8000
echo.
echo Presiona Ctrl+C para detener el servidor
echo.
echo ========================================
echo.

REM Iniciar servidor con acceso a red
python manage.py runserver 0.0.0.0:8000

