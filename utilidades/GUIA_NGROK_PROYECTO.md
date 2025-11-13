# 🌐 Guía de ngrok en ZenMindConnect

## 📍 Ubicación de ngrok

**ngrok está instalado en:**
```
C:\ngrok\ngrok.exe
```

✅ **Estado:** Instalado y listo para usar

---

## 🚀 Cómo Usar ngrok

### Opción 1: Script Automático (RECOMENDADO)

**Iniciar Django + ngrok juntos:**
```bash
INICIAR_TODO.bat
```

Este script:
1. ✅ Inicia Django en una ventana
2. ✅ Inicia ngrok en otra ventana
3. ✅ Te muestra la URL HTTPS pública

**Solo ngrok (si Django ya está corriendo):**
```bash
scripts\INICIAR_NGROK_SIMPLE.bat
```

### Opción 2: Manual

**Terminal 1 - Django:**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - ngrok:**
```bash
C:\ngrok\ngrok.exe http 8000
```

O si está en el PATH:
```bash
ngrok http 8000
```

---

## 📋 Scripts Disponibles

Todos los scripts están en la carpeta `scripts/`:

### Scripts Principales
- **`INICIAR_TODO.bat`** - Inicia Django + ngrok automáticamente
- **`INICIAR_NGROK_SIMPLE.bat`** - Inicia solo ngrok (simple)
- **`INICIAR_NGROK.bat`** - Inicia ngrok (con verificaciones)

### Scripts de Configuración
- **`INSTALAR_NGROK.bat`** - Instala y configura ngrok
- **`CONFIGURAR_AUTHTOKEN.bat`** - Configura el authtoken de ngrok
- **`VERIFICAR_INSTALACION.bat`** - Verifica que ngrok esté instalado

### Scripts de Utilidad
- **`OBTENER_URL_NGROK.bat`** - Obtiene la URL pública de ngrok
- **`VER_URL_NGROK.bat`** - Muestra la URL de ngrok
- **`ACTUALIZAR_ALLOWED_HOSTS.bat`** - Actualiza ALLOWED_HOSTS con dominio de ngrok

### Scripts Especiales
- **`INICIAR_VIDEOLLAMADA.bat`** - Inicia Django + ngrok para videollamadas
- **`INICIAR_TODO_SIMPLE.bat`** - Versión simple de INICIAR_TODO.bat
- **`INICIAR_TODO_FINAL.bat`** - Versión final con todas las verificaciones

---

## 🔧 Configuración

### 1. Authtoken de ngrok (OBLIGATORIO)

ngrok ahora requiere una cuenta gratuita. Para configurar:

**Opción A: Script automático**
```bash
scripts\CONFIGURAR_AUTHTOKEN.bat
```

**Opción B: Manual**
1. Crea cuenta en: https://dashboard.ngrok.com/signup
2. Obtén tu authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
3. Configura:
```bash
C:\ngrok\ngrok.exe config add-authtoken TU_AUTHTOKEN
```

### 2. ALLOWED_HOSTS

El proyecto ya está configurado para aceptar dominios de ngrok. Si necesitas actualizarlo:

```bash
scripts\ACTUALIZAR_ALLOWED_HOSTS.bat
```

O manualmente en `.env`:
```
ALLOWED_HOSTS=localhost,127.0.0.1,*.ngrok.io,*.ngrok-free.app
```

---

## 📱 Uso de la URL de ngrok

Cuando inicies ngrok, verás algo como:

```
Forwarding   https://abc123.ngrok-free.dev -> http://localhost:8000
```

### **Usa esa URL en:**
- ✅ Tu PC: `https://abc123.ngrok-free.dev`
- ✅ Tu celular: `https://abc123.ngrok-free.dev` (desde cualquier lugar)
- ✅ Cualquier dispositivo con internet

### **Ventajas:**
- ✅ HTTPS automático (necesario para cámara/micrófono)
- ✅ Funciona desde cualquier lugar (no requiere misma red WiFi)
- ✅ No requiere configuración de firewall
- ✅ Fácil de compartir

---

## 🎯 Casos de Uso

### 1. Probar Videollamadas desde Celular
```bash
INICIAR_TODO.bat
```
Luego usa la URL HTTPS de ngrok en tu celular.

### 2. Compartir con Cliente/Amigo
```bash
scripts\INICIAR_NGROK_SIMPLE.bat
```
Comparte la URL HTTPS que ngrok te da.

### 3. Desarrollo con HTTPS Local
```bash
python manage.py runserver 0.0.0.0:8000
# En otra terminal:
C:\ngrok\ngrok.exe http 8000
```

---

## ⚠️ Notas Importantes

### Seguridad
- ⚠️ ngrok expone tu servidor públicamente mientras esté activo
- ✅ Se cierra cuando cierras ngrok
- ✅ No compartas la URL públicamente
- ✅ Cierra ngrok cuando no lo uses

### URL Dinámica
- Con cuenta gratuita: La URL cambia cada vez que reinicias ngrok
- Con cuenta de pago: Puedes usar una URL fija

### Límites de Cuenta Gratuita
- ✅ Túnel HTTP/HTTPS
- ✅ 1 túnel simultáneo
- ✅ URL dinámica
- ⚠️ Límite de conexiones (suficiente para desarrollo)

---

## 🐛 Solución de Problemas

### "ngrok: command not found"
```bash
# Verificar que existe:
Test-Path C:\ngrok\ngrok.exe

# Si no existe, instalar:
scripts\INSTALAR_NGROK.bat
```

### "Tunnel session failed"
- Verifica que Django esté corriendo en puerto 8000
- Cierra otros programas que usen el puerto 8000
- Verifica tu conexión a internet

### "DisallowedHost" error
```bash
# Actualizar ALLOWED_HOSTS:
scripts\ACTUALIZAR_ALLOWED_HOSTS.bat
```

### "ngrok requires authentication"
```bash
# Configurar authtoken:
scripts\CONFIGURAR_AUTHTOKEN.bat
```

### La URL no funciona
- Espera 5-10 segundos después de iniciar ngrok
- Verifica que Django esté corriendo
- Usa la URL HTTPS (no HTTP)

---

## 📚 Documentación Adicional

- **`utilidades/GUIA_COMPLETA_NGROK.md`** - Guía completa y detallada
- **`utilidades/CONFIGURAR_NGROK_AUTH.md`** - Configuración de autenticación
- **`utilidades/ANALISIS_SEGURIDAD_NGROK.md`** - Análisis de seguridad
- **`scripts/README.md`** - Documentación de todos los scripts

---

## ✅ Resumen Rápido

1. **Iniciar todo automáticamente:**
   ```bash
   INICIAR_TODO.bat
   ```

2. **Solo ngrok (si Django ya está corriendo):**
   ```bash
   scripts\INICIAR_NGROK_SIMPLE.bat
   ```

3. **Copiar la URL HTTPS que ngrok muestra**

4. **Usar esa URL en cualquier dispositivo**

5. **¡Listo!** 🎉

---

**Ubicación:** `C:\ngrok\ngrok.exe`  
**Scripts:** `scripts/`  
**Documentación:** `utilidades/`

