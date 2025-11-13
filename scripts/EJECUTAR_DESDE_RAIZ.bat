@echo off
REM Este script asegura que todos los scripts se ejecuten desde la raíz del proyecto
REM Coloca este script en la raíz y úsalo para ejecutar otros scripts

if "%~1"=="" (
    echo Uso: EJECUTAR_DESDE_RAIZ.bat [nombre_script.bat]
    echo.
    echo Ejemplo: EJECUTAR_DESDE_RAIZ.bat scripts\REINICIAR_DJANGO.bat
    exit /b 1
)

call "%~1"
pause

