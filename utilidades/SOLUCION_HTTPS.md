# 🔒 Solución: Error "can not find getUserMedia"

## ❌ Problema

Los navegadores modernos bloquean el acceso a cámara/micrófono cuando no es HTTPS o localhost. Al acceder desde `192.168.1.83:8000`, el navegador no lo considera "seguro".

## ✅ Solución 1: Usar ngrok (RECOMENDADO)

ngrok crea un túnel HTTPS automáticamente.

### Paso 1: Instalar ngrok
1. Descarga: https://ngrok.com/download
2. Extrae el archivo `ngrok.exe` en una carpeta (ej: `C:\ngrok\`)
3. O instala con chocolatey: `choco install ngrok`

### Paso 2: Ejecutar Django normalmente
```bash
python manage.py runserver
```

### Paso 3: En otra terminal, ejecutar ngrok
```bash
ngrok http 8000
```

### Paso 4: Usar la URL de ngrok
ngrok te dará una URL como: `https://abc123.ngrok.io`

- **Tu PC:** `https://abc123.ngrok.io`
- **Celular:** `https://abc123.ngrok.io` (desde cualquier lugar con internet)

✅ **Ventajas:**
- HTTPS automático
- Funciona desde cualquier dispositivo con internet
- No requiere configuración de firewall

---

## ✅ Solución 2: Permitir acceso inseguro en Chrome (Solo desarrollo)

⚠️ **ADVERTENCIA:** Solo para desarrollo. No usar en producción.

### En Chrome (PC):
1. Abre Chrome
2. Ve a: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
3. Agrega: `http://192.168.1.83:8000`
4. Cambia el dropdown a "Enabled"
5. Reinicia Chrome

### En Chrome Mobile (Celular):
1. Abre Chrome
2. Ve a: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
3. Agrega: `http://192.168.1.83:8000`
4. Cambia a "Enabled"
5. Reinicia Chrome

⚠️ **Nota:** Esto puede no funcionar en todos los dispositivos móviles.

---

## ✅ Solución 3: Configurar HTTPS local (Avanzado)

Requiere generar certificados SSL. Más complejo pero más seguro.

---

## 🎯 Recomendación

**Usa ngrok** - Es la solución más simple y funciona perfectamente para desarrollo.

