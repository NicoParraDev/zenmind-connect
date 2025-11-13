@echo off
title ZenMindConnect - Videollamada
color 0A

echo.
echo ========================================
echo   ZENMINDCONNECT - VIDEOCALL
echo ========================================
echo.

REM Agregar C:\ngrok al PATH
set PATH=%PATH%;C:\ngrok

REM Verificar authtoken
C:\ngrok\ngrok.exe config check >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: ngrok no esta configurado
    echo.
    echo Ejecuta: CONFIGURAR_AUTHTOKEN.bat
    pause
    exit /b 1
)

echo ✓ ngrok configurado correctamente
echo.

REM Verificar Django
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% neq 0 (
    echo Iniciando Django...
    start "Django Server" cmd /k "title Django Server && color 0B && echo. && echo Django corriendo en http://127.0.0.1:8000 && echo. && python manage.py runserver"
    echo Esperando 5 segundos...
    timeout /t 5 /nobreak >nul
) else (
    echo ✓ Django ya esta corriendo
)

echo.
echo ========================================
echo   INICIANDO NGROK
echo ========================================
echo.
echo Django: http://127.0.0.1:8000
echo.
echo ========================================
echo   IMPORTANTE
echo ========================================
echo.
echo ngrok mostrara una URL HTTPS como:
echo   https://abc123.ngrok.io
echo.
echo USA ESA URL EN AMBOS DISPOSITIVOS:
echo   - Tu PC: https://abc123.ngrok.io
echo   - Celular: https://abc123.ngrok.io
echo.
echo ========================================
echo.
echo Presiona Ctrl+C para detener ngrok
echo.
echo ========================================
echo.

C:\ngrok\ngrok.exe http 8000

