@echo off
echo ========================================
echo   INICIAR SERVIDOR Y NGROK
echo ========================================
echo.

REM Verificar ngrok
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

REM Verificar .env
if not exist .env (
    echo ERROR: No se encontro el archivo .env
    pause
    exit /b 1
)

REM Actualizar ALLOWED_HOSTS si es necesario
findstr /C:"ngrok.io" .env >nul
if %errorlevel% neq 0 (
    echo Actualizando ALLOWED_HOSTS para ngrok...
    powershell -Command "$content = Get-Content .env; if ($content -notmatch 'ALLOWED_HOSTS.*ngrok') { $content = $content -replace 'ALLOWED_HOSTS=.*', 'ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83,*.ngrok.io,*.ngrok-free.app' } else { $content = $content -replace 'ALLOWED_HOSTS=.*', 'ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83,*.ngrok.io,*.ngrok-free.app' }; Set-Content .env $content"
    echo ✓ ALLOWED_HOSTS actualizado para ngrok
)

echo.
echo ========================================
echo   INICIANDO SERVIDOR DJANGO
echo ========================================
echo.

REM Iniciar Django en segundo plano
start "Django Server" cmd /k "python manage.py runserver"

echo Esperando 3 segundos para que Django inicie...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   INICIANDO NGROK
echo ========================================
echo.
echo Django esta corriendo en: http://127.0.0.1:8000
echo.
echo ngrok creara un tunel HTTPS.
echo.
echo IMPORTANTE:
echo - Copia la URL HTTPS que ngrok te muestra
echo - Usa esa URL en ambos dispositivos
echo - La URL sera algo como: https://abc123.ngrok.io
echo.
echo Presiona Ctrl+C para detener ngrok
echo (Django seguira corriendo en la otra ventana)
echo.
echo ========================================
echo.

ngrok http 8000

