@echo off
title Configurar ngrok Authtoken
color 0B

echo.
echo ========================================
echo   CONFIGURAR NGROK AUTHTOKEN
echo ========================================
echo.
echo ngrok requiere una cuenta gratuita.
echo.
echo PASOS:
echo 1. Ve a: https://dashboard.ngrok.com/signup
echo 2. Registrate con tu email (es gratis)
echo 3. Verifica tu email
echo 4. Ve a: https://dashboard.ngrok.com/get-started/your-authtoken
echo 5. Copia tu authtoken
echo.
echo ========================================
echo.

set /p authtoken="Pega tu authtoken aqui: "

if "%authtoken%"=="" (
    echo ERROR: No ingresaste un authtoken
    pause
    exit /b 1
)

echo.
echo Configurando authtoken...

REM Agregar C:\ngrok al PATH
set PATH=%PATH%;C:\ngrok

REM Configurar authtoken
if exist "C:\ngrok\ngrok.exe" (
    C:\ngrok\ngrok.exe config add-authtoken %authtoken%
) else (
    ngrok config add-authtoken %authtoken%
)

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   ✓ AUTHTOKEN CONFIGURADO
    echo ========================================
    echo.
    echo Ya puedes usar ngrok normalmente.
    echo.
    echo Ejecuta: INICIAR_NGROK_SIMPLE.bat
    echo.
) else (
    echo.
    echo ERROR: No se pudo configurar el authtoken
    echo Verifica que el authtoken sea correcto
    echo.
)

pause

