@echo off
REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."

echo ========================================
echo   REINICIANDO DJANGO
echo ========================================
echo.

REM Detener procesos de Django existentes
echo Deteniendo procesos de Django existentes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *runserver*" 2>nul
timeout /t 2 /nobreak >nul

REM Iniciar Django en 0.0.0.0:8000 para ngrok
echo.
echo Iniciando Django en 0.0.0.0:8000...
echo.
python manage.py runserver 0.0.0.0:8000

pause

