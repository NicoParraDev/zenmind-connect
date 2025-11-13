@echo off
echo ========================================
echo   SERVIDOR DJANGO - ACCESO RED LOCAL
echo ========================================
echo.
echo El servidor estara disponible en:
echo   - Local: http://127.0.0.1:8000
echo   - Red local: http://192.168.1.83:8000
echo.
echo Desde otro dispositivo en la misma red, accede con:
echo   http://192.168.1.83:8000
echo.
echo Presiona Ctrl+C para detener el servidor
echo.
python manage.py runserver 0.0.0.0:8000

