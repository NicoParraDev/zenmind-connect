@echo off
echo ========================================
echo Iniciando Django con WebSockets (Daphne)
echo ========================================
echo.

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Instalar dependencias si es necesario
echo Verificando dependencias...
pip install -q channels==4.0.0 channels-redis==4.1.0 daphne==4.0.0

echo.
echo Iniciando servidor con Daphne (soporta WebSockets)...
echo.
daphne -b 0.0.0.0 -p 8000 ZenMindConnect.asgi:application

pause

