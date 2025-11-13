#!/bin/bash
# Script para iniciar videollamada desde Git Bash

echo "========================================"
echo "  ZENMINDCONNECT - VIDEOCALL"
echo "  Iniciando servidor y ngrok"
echo "========================================"
echo ""

# Agregar C:\ngrok al PATH
export PATH="$PATH:/c/ngrok"

# Verificar ngrok
if command -v ngrok &> /dev/null || [ -f "/c/ngrok/ngrok.exe" ]; then
    echo "✓ ngrok encontrado"
else
    echo "ERROR: ngrok no encontrado"
    echo "Por favor ejecuta: INSTALAR_NGROK.bat desde CMD"
    exit 1
fi

# Verificar .env
if [ ! -f .env ]; then
    echo "ERROR: No se encontro el archivo .env"
    exit 1
fi

echo ""
echo "========================================"
echo "  INICIANDO SERVIDOR DJANGO"
echo "========================================"
echo ""

# Iniciar Django en background
echo "Iniciando Django..."
python manage.py runserver &
DJANGO_PID=$!

echo "Esperando 5 segundos para que Django inicie..."
sleep 5

echo ""
echo "========================================"
echo "  INICIANDO NGROK - TUNEL HTTPS"
echo "========================================"
echo ""
echo "Django esta corriendo en: http://127.0.0.1:8000"
echo ""
echo "========================================"
echo "  IMPORTANTE"
echo "========================================"
echo ""
echo "ngrok creara un tunel HTTPS publico."
echo ""
echo "PASOS:"
echo "1. ngrok mostrara una URL como: https://abc123.ngrok.io"
echo "2. Copia esa URL HTTPS"
echo "3. Usa esa URL en AMBOS dispositivos:"
echo "   - Tu PC: https://abc123.ngrok.io"
echo "2. Celular: https://abc123.ngrok.io"
echo ""
echo "========================================"
echo ""
echo "Presiona Ctrl+C para detener ngrok y Django"
echo ""
echo "========================================"
echo ""

# Iniciar ngrok
if command -v ngrok &> /dev/null; then
    ngrok http 8000
else
    /c/ngrok/ngrok.exe http 8000
fi

# Limpiar al salir
kill $DJANGO_PID 2>/dev/null

