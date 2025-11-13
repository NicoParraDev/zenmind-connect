@echo off
echo ========================================
echo   ACTUALIZANDO ALLOWED_HOSTS
echo ========================================
echo.

REM Obtener dominio actual de ngrok si esta corriendo
set NGROK_DOMAIN=
curl -s http://localhost:4040/api/tunnels 2>nul | findstr "public_url" >nul
if %errorlevel% equ 0 (
    echo Obteniendo dominio de ngrok...
    for /f "tokens=*" %%a in ('curl -s http://localhost:4040/api/tunnels ^| findstr "public_url"') do (
        set line=%%a
        set line=!line:*"public_url": "=!
        set line=!line:https://=!
        set line=!line:/"=!
        set NGROK_DOMAIN=!line!
    )
)

if defined NGROK_DOMAIN (
    echo Dominio detectado: %NGROK_DOMAIN%
    powershell -Command "$content = Get-Content .env; if ($content -notmatch '%NGROK_DOMAIN%') { $content = $content -replace 'ALLOWED_HOSTS=.*', 'ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83,*.ngrok.io,*.ngrok-free.app,%NGROK_DOMAIN%'; Set-Content .env $content; Write-Host '✓ ALLOWED_HOSTS actualizado con dominio de ngrok' } else { Write-Host '✓ ALLOWED_HOSTS ya incluye el dominio' }"
) else (
    echo Actualizando ALLOWED_HOSTS con patrones de ngrok...
    powershell -Command "$content = Get-Content .env; $content = $content -replace 'ALLOWED_HOSTS=.*', 'ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83,*.ngrok.io,*.ngrok-free.app'; Set-Content .env $content"
    echo ✓ ALLOWED_HOSTS actualizado
)

echo.
echo IMPORTANTE: Debes REINICIAR Django para que los cambios surtan efecto
echo.
pause

