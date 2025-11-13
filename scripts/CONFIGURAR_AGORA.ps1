# Script para configurar credenciales de Agora
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURAR CREDENCIALES DE AGORA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Este script te ayudará a configurar tus credenciales de Agora en el archivo .env" -ForegroundColor Yellow
Write-Host ""

# Verificar que el archivo .env existe
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: El archivo .env no existe en la raíz del proyecto" -ForegroundColor Red
    Write-Host "Por favor, crea el archivo .env copiando env.example" -ForegroundColor Yellow
    Write-Host "Ejecuta: Copy-Item env.example .env" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Solicitar credenciales
$appId = Read-Host "Ingresa tu AGORA_APP_ID"
$appCertificate = Read-Host "Ingresa tu AGORA_APP_CERTIFICATE"

if ([string]::IsNullOrWhiteSpace($appId)) {
    Write-Host "ERROR: AGORA_APP_ID no puede estar vacío" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

if ([string]::IsNullOrWhiteSpace($appCertificate)) {
    Write-Host "ERROR: AGORA_APP_CERTIFICATE no puede estar vacío" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "Actualizando archivo .env..." -ForegroundColor Yellow

# Leer el contenido del archivo
$content = Get-Content .env -Raw

# Reemplazar las credenciales
$content = $content -replace 'AGORA_APP_ID=.*', "AGORA_APP_ID=$appId"
$content = $content -replace 'AGORA_APP_CERTIFICATE=.*', "AGORA_APP_CERTIFICATE=$appCertificate"

# Guardar el archivo
Set-Content .env -Value $content -NoNewline

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  CONFIGURACIÓN EXITOSA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Las credenciales de Agora han sido actualizadas en el archivo .env" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANTE: Reinicia el servidor Django para que los cambios surtan efecto" -ForegroundColor Yellow
Write-Host ""
Read-Host "Presiona Enter para continuar"

