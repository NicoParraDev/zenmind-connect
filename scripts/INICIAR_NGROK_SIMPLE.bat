@echo off
title ngrok - Tunnel HTTPS
color 0A

echo.
echo ========================================
echo   NGROK - TUNEL HTTPS
echo ========================================
echo.

REM Agregar C:\ngrok al PATH
set PATH=%PATH%;C:\ngrok

REM Verificar que Django este corriendo
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% neq 0 (
    echo ERROR: Django no esta corriendo en el puerto 8000
    echo.
    echo Por favor, ejecuta primero:
    echo    python manage.py runserver
    echo.
    pause
    exit /b 1
)

echo ✓ Django detectado en puerto 8000
echo.
echo ========================================
echo   IMPORTANTE
echo ========================================
echo.
echo ngrok creara un tunel HTTPS publico.
echo.
echo PASOS:
echo 1. ngrok mostrara una URL como: https://abc123.ngrok.io
echo 2. Copia esa URL HTTPS
echo 3. Usa esa URL en AMBOS dispositivos:
echo    - Tu PC: https://abc123.ngrok.io
echo    - Celular: https://abc123.ngrok.io
echo.
echo ========================================
echo.
echo Presiona Ctrl+C para detener ngrok
echo.
echo ========================================
echo.

REM Iniciar ngrok
if exist "C:\ngrok\ngrok.exe" (
    C:\ngrok\ngrok.exe http 8000
) else (
    ngrok http 8000
)

