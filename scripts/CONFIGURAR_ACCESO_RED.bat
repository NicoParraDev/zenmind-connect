@echo off
echo ========================================
echo   CONFIGURAR ACCESO DESDE RED LOCAL
echo ========================================
echo.

REM Verificar si existe .env
if not exist .env (
    echo ERROR: No se encontro el archivo .env
    echo Por favor crea el archivo .env primero
    pause
    exit /b 1
)

echo [1/2] Verificando archivo .env...
echo.

REM Leer ALLOWED_HOSTS actual
findstr /C:"ALLOWED_HOSTS" .env >nul
if %errorlevel% equ 0 (
    echo ALLOWED_HOSTS encontrado en .env
    echo.
    echo Por favor, edita manualmente tu archivo .env y cambia:
    echo   ALLOWED_HOSTS=localhost,127.0.0.1
    echo.
    echo Por:
    echo   ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83
    echo.
) else (
    echo ALLOWED_HOSTS no encontrado, agregando...
    echo ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83 >> .env
    echo ✓ ALLOWED_HOSTS agregado
)

echo.
echo [2/2] Configuracion lista!
echo.
echo ========================================
echo   INSTRUCCIONES DE USO
echo ========================================
echo.
echo 1. Ejecuta el servidor con:
echo    python manage.py runserver 0.0.0.0:8000
echo.
echo    O usa: runserver_network.bat
echo.
echo 2. Desde tu PC (donde corre Django):
echo    http://127.0.0.1:8000
echo    http://localhost:8000
echo.
echo 3. Desde otro dispositivo (misma red WiFi):
echo    http://192.168.1.83:8000
echo.
echo ========================================
pause

