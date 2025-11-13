@echo off
title ZenMindConnect - Iniciar Todo
color 0A

echo.
echo ========================================
echo   ZENMINDCONNECT - INICIAR TODO
echo ========================================
echo.

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."

REM Verificar .env
if not exist .env (
    echo ERROR: No se encontro el archivo .env
    pause
    exit /b 1
)

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
        echo Por favor ejecuta: scripts\INSTALAR_NGROK.bat
        pause
        exit /b 1
    )
) else (
    set NGROK_PATH=ngrok
)

echo ========================================
echo   PASO 1: INICIANDO DJANGO
echo ========================================
echo.

REM Verificar si Django ya esta corriendo
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo ⚠ Django ya esta corriendo en el puerto 8000
    echo.
) else (
    echo Iniciando Django en nueva ventana...
    start "Django Server" cmd /k "title Django Server && color 0B && cd /d %~dp0.. && python manage.py runserver 0.0.0.0:8000"
    echo Esperando 5 segundos para que Django inicie...
    timeout /t 5 /nobreak >nul
)

echo.
echo ========================================
echo   PASO 2: INICIANDO NGROK
echo ========================================
echo.

echo Iniciando ngrok en nueva ventana...
start "Ngrok Tunnel" cmd /k "title Ngrok Tunnel && color 0E && %NGROK_PATH% http 8000"

echo.
echo ========================================
echo   ✓ TODO INICIADO
echo ========================================
echo.
echo Django: http://127.0.0.1:8000
echo.
echo IMPORTANTE:
echo 1. Espera 5-10 segundos a que ngrok genere la URL
echo 2. Ve a la ventana de ngrok y copia la URL HTTPS
echo 3. Usa esa URL en ambos navegadores:
echo    - Chrome normal: [URL de ngrok]
echo    - Chrome incógnito: [URL de ngrok]
echo.
echo Para probar localmente (sin ngrok):
echo    - Chrome normal: http://127.0.0.1:8000
echo    - Chrome incógnito: http://127.0.0.1:8000
echo.
pause

