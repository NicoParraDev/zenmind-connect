@echo off
REM Script para iniciar Django desde cualquier ubicación
REM Coloca este archivo en la raíz del proyecto

REM Cambiar al directorio del script
cd /d "%~dp0"

echo ========================================
echo   INICIANDO DJANGO
echo ========================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "manage.py" (
    echo ERROR: No se encontro manage.py
    echo Asegurate de que este script este en la raiz del proyecto
    pause
    exit /b 1
)

REM Detener procesos de Django existentes
echo Deteniendo procesos de Django existentes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *runserver*" 2>nul
timeout /t 2 /nobreak >nul

REM Iniciar Django
echo.
echo Iniciando Django en 0.0.0.0:8000...
echo.
python manage.py runserver 0.0.0.0:8000

pause

