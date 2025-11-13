@echo off
echo ========================================
echo   DETENIENDO SERVIDOR ACTUAL
echo ========================================
echo.

REM Buscar procesos de Python que estan usando el puerto 8000
echo Buscando procesos en el puerto 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Proceso encontrado: PID %%a
    echo Deteniendo proceso...
    taskkill /PID %%a /F >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ Proceso detenido
    ) else (
        echo ⚠ No se pudo detener el proceso (puede que ya este detenido)
    )
)

echo.
echo Esperando 2 segundos...
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   REINICIANDO SERVIDOR CON ACCESO A RED
echo ========================================
echo.

REM Verificar ALLOWED_HOSTS
findstr /C:"192.168.1.83" .env >nul
if %errorlevel% neq 0 (
    echo Actualizando ALLOWED_HOSTS en .env...
    powershell -Command "(Get-Content .env) -replace 'ALLOWED_HOSTS=localhost,127.0.0.1', 'ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83' | Set-Content .env"
    echo ✓ ALLOWED_HOSTS actualizado
) else (
    echo ✓ ALLOWED_HOSTS ya esta configurado
)

echo.
echo ========================================
echo   SERVIDOR INICIANDO...
echo ========================================
echo.
echo El servidor estara disponible en:
echo   - Local: http://127.0.0.1:8000
echo   - Red local: http://192.168.1.83:8000
echo.
echo Desde otro dispositivo en la misma red WiFi:
echo   http://192.168.1.83:8000
echo.
echo Presiona Ctrl+C para detener el servidor
echo.
echo ========================================
echo.

REM Iniciar servidor con acceso a red
python manage.py runserver 0.0.0.0:8000

