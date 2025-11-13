@echo off
echo ========================================
echo   VERIFICANDO INSTALACION
echo ========================================
echo.

REM Agregar C:\ngrok al PATH de esta sesion
set PATH=%PATH%;C:\ngrok

echo [1/3] Verificando ngrok...
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ ngrok encontrado
    ngrok version
) else (
    if exist "C:\ngrok\ngrok.exe" (
        echo ✓ ngrok encontrado en C:\ngrok\
        C:\ngrok\ngrok.exe version
    ) else (
        echo ✗ ngrok NO encontrado
        echo.
        echo Por favor ejecuta: INSTALAR_NGROK.bat
        pause
        exit /b 1
    )
)

echo.
echo [2/3] Verificando Django...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python encontrado
    python --version
) else (
    echo ✗ Python NO encontrado
)

echo.
echo [3/3] Verificando .env...
if exist .env (
    echo ✓ Archivo .env encontrado
    findstr /C:"ngrok" .env >nul
    if %errorlevel% equ 0 (
        echo ✓ ALLOWED_HOSTS configurado para ngrok
    ) else (
        echo ⚠ ALLOWED_HOSTS no incluye ngrok (se actualizara automaticamente)
    )
) else (
    echo ✗ Archivo .env NO encontrado
)

echo.
echo ========================================
echo   ESTADO: LISTO PARA USAR
echo ========================================
echo.
echo Para iniciar todo, ejecuta:
echo    INICIAR_TODO.bat
echo.
pause

