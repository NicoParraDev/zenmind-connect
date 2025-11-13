@echo off
echo ========================================
echo   CONFIGURAR CREDENCIALES DE AGORA
echo ========================================
echo.

echo Este script te ayudara a configurar tus credenciales de Agora en el archivo .env
echo.

set /p AGORA_APP_ID="Ingresa tu AGORA_APP_ID: "
set /p AGORA_APP_CERTIFICATE="Ingresa tu AGORA_APP_CERTIFICATE: "

if "%AGORA_APP_ID%"=="" (
    echo ERROR: AGORA_APP_ID no puede estar vacio
    pause
    exit /b 1
)

if "%AGORA_APP_CERTIFICATE%"=="" (
    echo ERROR: AGORA_APP_CERTIFICATE no puede estar vacio
    pause
    exit /b 1
)

echo.
echo Actualizando archivo .env...

REM Leer el archivo .env y reemplazar las credenciales
powershell -Command "$content = Get-Content .env -Raw; $content = $content -replace 'AGORA_APP_ID=.*', 'AGORA_APP_ID=%AGORA_APP_ID%'; $content = $content -replace 'AGORA_APP_CERTIFICATE=.*', 'AGORA_APP_CERTIFICATE=%AGORA_APP_CERTIFICATE%'; Set-Content .env -Value $content -NoNewline"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   CONFIGURACION EXITOSA!
    echo ========================================
    echo.
    echo Las credenciales de Agora han sido actualizadas en el archivo .env
    echo.
    echo IMPORTANTE: Reinicia el servidor Django para que los cambios surtan efecto
    echo.
) else (
    echo.
    echo ERROR: No se pudo actualizar el archivo .env
    echo Verifica que el archivo .env exista en la raiz del proyecto
    echo.
)

pause

