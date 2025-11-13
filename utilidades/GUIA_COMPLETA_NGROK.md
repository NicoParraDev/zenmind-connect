# 🚀 Guía Completa: Configurar ngrok para Videollamadas

## ❌ Problema

Los navegadores bloquean el acceso a cámara/micrófono cuando no es HTTPS. Al acceder desde `192.168.1.83:8000`, el navegador no lo considera "seguro".

## ✅ Solución: ngrok

ngrok crea un túnel HTTPS automáticamente, permitiendo acceso seguro desde cualquier dispositivo.

---

## 📥 Paso 1: Instalar ngrok

### Opción A: Descarga Manual (RECOMENDADO)

1. **Descarga ngrok:**
   - Ve a: https://ngrok.com/download
   - Descarga la versión para Windows

2. **Extrae ngrok.exe:**
   - Crea la carpeta: `C:\ngrok\`
   - Extrae `ngrok.exe` ahí

3. **Agregar al PATH (Opcional):**
   - Busca "Variables de entorno" en Windows
   - Agrega `C:\ngrok` al PATH
   - O simplemente coloca `ngrok.exe` en la carpeta del proyecto

### Opción B: Chocolatey (si lo tienes)
```bash
choco install ngrok
```

### Opción C: Scoop (si lo tienes)
```bash
scoop install ngrok
```

### Verificar instalación:
```bash
ngrok version
```

---

## ⚙️ Paso 2: Configurar Django

El script `INICIAR_TODO.bat` actualiza automáticamente `ALLOWED_HOSTS` para incluir dominios de ngrok.

O manualmente, edita `.env`:
```
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83,*.ngrok.io,*.ngrok-free.app
```

---

## 🚀 Paso 3: Iniciar Todo

### Opción A: Script Automático (RECOMENDADO)

Ejecuta:
```bash
INICIAR_TODO.bat
```

Este script:
1. ✅ Inicia Django en una ventana
2. ✅ Espera a que Django esté listo
3. ✅ Inicia ngrok en esta ventana
4. ✅ Te muestra la URL HTTPS

### Opción B: Manual

**Terminal 1 - Django:**
```bash
python manage.py runserver
```

**Terminal 2 - ngrok:**
```bash
ngrok http 8000
```

O usa: `INICIAR_NGROK.bat`

---

## 📱 Paso 4: Usar la URL de ngrok

ngrok mostrará algo como:

```
Forwarding   https://abc123.ngrok.io -> http://localhost:8000
```

### **Usa esa URL en ambos dispositivos:**

- **Tu PC:** `https://abc123.ngrok.io`
- **Celular:** `https://abc123.ngrok.io` (desde cualquier lugar con internet)

---

## ✅ Ventajas de ngrok

- ✅ HTTPS automático (navegadores permiten cámara/micrófono)
- ✅ Funciona desde cualquier dispositivo con internet
- ✅ No requiere configuración de firewall
- ✅ No requiere estar en la misma red WiFi
- ✅ Fácil de usar

---

## 🆘 Problemas Comunes

### "ngrok: command not found"
- Verifica que ngrok.exe esté en `C:\ngrok\` o en el PATH
- O coloca `ngrok.exe` en la carpeta del proyecto

### "Tunnel session failed"
- Verifica que Django esté corriendo en el puerto 8000
- Cierra otros programas que usen el puerto 8000

### "DisallowedHost" error
- Verifica que `ALLOWED_HOSTS` en `.env` incluya `*.ngrok.io`

### La URL cambia cada vez
- Con cuenta gratuita, la URL cambia cada vez que reinicias ngrok
- Con cuenta de pago, puedes usar una URL fija

---

## 📝 Resumen Rápido

1. ✅ Instala ngrok: `INSTALAR_NGROK.bat`
2. ✅ Inicia todo: `INICIAR_TODO.bat`
3. ✅ Copia la URL HTTPS de ngrok
4. ✅ Usa esa URL en ambos dispositivos
5. ✅ ¡Listo! Ya puedes probar la videollamada

---

## 🎯 URLs

- **Django local:** `http://127.0.0.1:8000` (solo tu PC)
- **ngrok HTTPS:** `https://abc123.ngrok.io` (cualquier dispositivo)

