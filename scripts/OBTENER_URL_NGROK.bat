@echo off
echo ========================================
echo   OBTENER URL DE NGROK
echo ========================================
echo.

REM Esperar un momento
timeout /t 2 /nobreak >nul

REM Intentar obtener URL via API
curl -s http://localhost:4040/api/tunnels 2>nul | findstr "public_url" >nul
if %errorlevel% equ 0 (
    echo ✓ ngrok esta corriendo
    echo.
    echo URL HTTPS:
    curl -s http://localhost:4040/api/tunnels | findstr "public_url"
    echo.
    echo Copia la URL que empieza con https://
) else (
    echo ngrok NO esta corriendo o aun no ha iniciado
    echo.
    echo Por favor ejecuta: INICIAR_TODO_FINAL.bat
    echo.
    echo O manualmente:
    echo    C:\ngrok\ngrok.exe http 8000
)

echo.
pause

