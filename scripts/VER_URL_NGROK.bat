@echo off
echo ========================================
echo   VERIFICANDO URL DE NGROK
echo ========================================
echo.

REM Intentar obtener URL de ngrok via API
curl -s http://localhost:4040/api/tunnels >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ ngrok esta corriendo
    echo.
    echo Obteniendo URL...
    echo.
    curl -s http://localhost:4040/api/tunnels | findstr "public_url"
    echo.
    echo Si ves una URL https://, esa es la que debes usar
) else (
    echo ngrok NO esta corriendo
    echo.
    echo Por favor ejecuta: INICIAR_NGROK_SIMPLE.bat
)

echo.
pause

