@echo off
title ZenMindConnect - Videollamada con ngrok
color 0A

echo.
echo ========================================
echo   ZENMINDCONNECT - VIDEOCALL
echo   Iniciando servidor y ngrok
echo ========================================
echo.

REM Agregar C:\ngrok al PATH
set PATH=%PATH%;C:\ngrok

REM Verificar ngrok
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\ngrok\ngrok.exe" (
        set NGROK_PATH=C:\ngrok\ngrok.exe
    ) else (
        echo ERROR: ngrok no encontrado
        echo.
        echo Por favor ejecuta: INSTALAR_NGROK.bat
        pause
        exit /b 1
    )
) else (
    set NGROK_PATH=ngrok
)

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."

REM Verificar .env
if not exist .env (
    echo ERROR: No se encontro el archivo .env
    pause
    exit /b 1
)

REM Actualizar ALLOWED_HOSTS para ngrok
findstr /C:"ngrok" .env >nul
if %errorlevel% neq 0 (
    echo Actualizando ALLOWED_HOSTS para ngrok...
    powershell -Command "$content = Get-Content .env; $content = $content -replace 'ALLOWED_HOSTS=.*', 'ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83,*.ngrok.io,*.ngrok-free.app'; Set-Content .env $content"
    echo ✓ ALLOWED_HOSTS actualizado
)

echo.
echo ========================================
echo   INICIANDO SERVIDOR DJANGO
echo ========================================
echo.

REM Verificar si Django ya esta corriendo
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo ⚠ Django ya esta corriendo en el puerto 8000
    echo.
    set /p continuar="¿Deseas continuar de todos modos? (S/N): "
    if /i not "%continuar%"=="S" exit /b 1
)

REM Iniciar Django en nueva ventana
echo Iniciando Django en nueva ventana...
start "Django Server - ZenMindConnect" cmd /k "title Django Server && color 0B && echo. && echo ======================================== && echo   DJANGO SERVER && echo ======================================== && echo. && echo Servidor corriendo en: http://127.0.0.1:8000 && echo. && echo Presiona Ctrl+C para detener && echo. && python manage.py runserver"

echo Esperando 5 segundos para que Django inicie...
timeout /t 5 /nobreak >nul

REM Verificar que Django este corriendo
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% neq 0 (
    echo ⚠ ADVERTENCIA: Django no parece estar corriendo
    echo Esperando 5 segundos mas...
    timeout /t 5 /nobreak >nul
)

echo.
echo ========================================
echo   INICIANDO NGROK - TUNEL HTTPS
echo ========================================
echo.
echo Django esta corriendo en: http://127.0.0.1:8000
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
echo (Django seguira corriendo en la otra ventana)
echo.
echo ========================================
echo.

REM Iniciar ngrok
%NGROK_PATH% http 8000

