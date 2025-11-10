@echo off
echo ========================================
echo   SETUP RAPIDO - ZenMindConnect
echo ========================================
echo.

echo [1/5] Verificando archivo .env...
if not exist .env (
    echo Creando .env desde env.example...
    copy env.example .env
    echo ✓ Archivo .env creado
    echo ⚠ IMPORTANTE: Edita .env con tus valores reales
) else (
    echo ✓ Archivo .env ya existe
)
echo.

echo [2/5] Instalando dependencias...
pip install -r requirements.txt
echo.

echo [3/5] Verificando directorio logs...
if not exist logs mkdir logs
echo ✓ Directorio logs listo
echo.

echo [4/5] Aplicando migraciones...
python manage.py makemigrations
python manage.py migrate
echo.

echo [5/5] ¿Crear superusuario? (S/N)
set /p crear_super="> "
if /i "%crear_super%"=="S" (
    python manage.py createsuperuser
)
echo.

echo ========================================
echo   SETUP COMPLETADO
echo ========================================
echo.
echo Para levantar el servidor ejecuta:
echo   python manage.py runserver
echo.
pause

