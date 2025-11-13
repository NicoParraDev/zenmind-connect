@echo off
echo ========================================
echo   CONFIGURAR NGROK PARA HTTPS
echo ========================================
echo.

REM Verificar si ngrok existe
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: ngrok no esta instalado
    echo.
    echo Por favor:
    echo 1. Descarga ngrok de: https://ngrok.com/download
    echo 2. Extrae ngrok.exe en una carpeta
    echo 3. Agrega la carpeta al PATH o coloca ngrok.exe en esta carpeta
    echo.
    echo O instala con chocolatey:
    echo    choco install ngrok
    echo.
    pause
    exit /b 1
)

echo ✓ ngrok encontrado
echo.
echo ========================================
echo   INSTRUCCIONES
echo ========================================
echo.
echo 1. Asegurate de que Django este corriendo:
echo    python manage.py runserver
echo.
echo 2. En esta ventana, ejecuta:
echo    ngrok http 8000
echo.
echo 3. ngrok te dara una URL como:
echo    https://abc123.ngrok.io
echo.
echo 4. Usa esa URL en ambos dispositivos:
echo    - Tu PC: https://abc123.ngrok.io
echo    - Celular: https://abc123.ngrok.io
echo.
echo ========================================
echo   EJECUTANDO NGROK...
echo ========================================
echo.
echo Presiona Ctrl+C para detener ngrok
echo.

ngrok http 8000

