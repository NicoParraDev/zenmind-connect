@echo off
echo ========================================
echo   INSTALAR Y CONFIGURAR NGROK
echo ========================================
echo.

REM Verificar si ngrok ya existe
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ ngrok ya esta instalado
    ngrok version
    echo.
    goto :configurar
)

echo [1/3] Verificando si ngrok esta instalado...
echo.

REM Verificar si existe en carpeta comun
if exist "C:\ngrok\ngrok.exe" (
    echo ✓ ngrok encontrado en C:\ngrok\
    set PATH=%PATH%;C:\ngrok
    goto :configurar
)

echo ngrok NO esta instalado.
echo.
echo ========================================
echo   OPCIONES DE INSTALACION
echo ========================================
echo.
echo Opcion 1: Descarga manual (RECOMENDADO)
echo   1. Ve a: https://ngrok.com/download
echo   2. Descarga ngrok para Windows
echo   3. Extrae ngrok.exe en: C:\ngrok\
echo   4. Ejecuta este script de nuevo
echo.
echo Opcion 2: Chocolatey (si lo tienes instalado)
echo   choco install ngrok
echo.
echo Opcion 3: Scoop (si lo tienes instalado)
echo   scoop install ngrok
echo.
echo ========================================
echo.
pause
exit /b 1

:configurar
echo.
echo [2/3] Configurando ngrok...
echo.

REM Crear directorio si no existe
if not exist "%USERPROFILE%\.ngrok" mkdir "%USERPROFILE%\.ngrok"

echo ✓ Configuracion lista
echo.
echo [3/3] Listo para usar!
echo.
echo ========================================
echo   USO DE NGROK
echo ========================================
echo.
echo 1. Asegurate de que Django este corriendo:
echo    python manage.py runserver
echo.
echo 2. Ejecuta: INICIAR_NGROK.bat
echo.
echo 3. Usa la URL HTTPS que ngrok te da
echo.
echo ========================================
pause

