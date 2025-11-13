@echo off
echo ========================================
echo   INICIANDO NGROK - TUNEL HTTPS
echo ========================================
echo.

REM Verificar si Django esta corriendo
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% neq 0 (
    echo ⚠ ADVERTENCIA: Django no parece estar corriendo en el puerto 8000
    echo.
    echo Por favor, ejecuta primero:
    echo    python manage.py runserver
    echo.
    echo Luego ejecuta este script de nuevo
    echo.
    pause
    exit /b 1
)

echo ✓ Django detectado en puerto 8000
echo.

REM Verificar si ngrok existe
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\ngrok\ngrok.exe" (
        set PATH=%PATH%;C:\ngrok
    ) else (
        echo ERROR: ngrok no esta instalado
        echo.
        echo Por favor ejecuta primero: INSTALAR_NGROK.bat
        echo.
        pause
        exit /b 1
    )
)

echo ========================================
echo   NGROK INICIANDO...
echo ========================================
echo.
echo El servidor Django debe estar corriendo en:
echo   http://127.0.0.1:8000
echo.
echo ngrok creara un tunel HTTPS publico.
echo.
echo IMPORTANTE:
echo - Copia la URL HTTPS que ngrok te muestra
echo - Usa esa URL en ambos dispositivos (PC y celular)
echo - La URL sera algo como: https://abc123.ngrok.io
echo.
echo Presiona Ctrl+C para detener ngrok
echo.
echo ========================================
echo.

ngrok http 8000

