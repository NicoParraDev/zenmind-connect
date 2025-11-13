# 🚀 Guía Rápida: Probar Videollamada desde Dos Dispositivos

## ✅ Recomendación: Opción 1 (Modificar .env)

Esta es la opción más simple y no requiere software adicional.

---

## 📝 Paso 1: Configurar .env

Edita tu archivo `.env` y modifica la línea `ALLOWED_HOSTS`:

**ANTES:**
```
ALLOWED_HOSTS=localhost,127.0.0.1
```

**DESPUÉS:**
```
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83
```

O ejecuta el script: `CONFIGURAR_ACCESO_RED.bat`

---

## 🖥️ Paso 2: Ejecutar el Servidor

Ejecuta el servidor con acceso a red local:

```bash
python manage.py runserver 0.0.0.0:8000
```

O usa el script:
```bash
runserver_network.bat
```

---

## 📱 Paso 3: Acceder desde Cada Dispositivo

### **TÚ (desde tu PC donde corre Django):**
- Abre el navegador
- Ve a: `http://127.0.0.1:8000` o `http://localhost:8000`
- Inicia sesión con un usuario (ej: `usuario` / `usuario123`)

### **OTRO DISPOSITIVO (teléfono, tablet, otra PC en la misma WiFi):**
- Abre el navegador
- Ve a: `http://192.168.1.83:8000`
- Inicia sesión con otro usuario (ej: `testuser` / `test123`)

---

## 🎥 Paso 4: Probar la Videollamada

1. Ambos usuarios deben estar en la misma sala de videollamada
2. Cada uno verá su propia cámara
3. Cada uno debería ver la cámara del otro

---

## ⚠️ Notas Importantes

- ✅ Ambos dispositivos deben estar en la **misma red WiFi**
- ✅ Si tu IP cambia (reinicio de router), verifica con `ipconfig` y actualiza `.env`
- ✅ Si tienes firewall, permite el puerto 8000
- ✅ La IP `192.168.1.83` es específica de tu PC - puede ser diferente en otra red

---

## 🔄 Si la IP Cambia

Si tu IP local cambia, ejecuta:
```bash
ipconfig | findstr /i "IPv4"
```

Y actualiza `ALLOWED_HOSTS` en `.env` con la nueva IP.

---

## 🆘 Problemas Comunes

**"DisallowedHost" error:**
- Verifica que `ALLOWED_HOSTS` en `.env` incluya tu IP local

**No puedo acceder desde otro dispositivo:**
- Verifica que ambos estén en la misma red WiFi
- Verifica que el firewall permita el puerto 8000
- Verifica que el servidor esté corriendo con `0.0.0.0:8000` (no solo `127.0.0.1:8000`)

