# 🚀 INICIO RÁPIDO - Configurar Todo para Videollamadas

## ✅ TODO ESTÁ LISTO - Solo sigue estos pasos:

---

## 📥 Paso 1: Instalar ngrok

**Ejecuta:**
```bash
INSTALAR_NGROK.bat
```

Este script te guiará. Si ngrok no está instalado:
1. Ve a: https://ngrok.com/download
2. Descarga ngrok para Windows
3. Extrae `ngrok.exe` en: `C:\ngrok\`
4. Ejecuta `INSTALAR_NGROK.bat` de nuevo

---

## 🚀 Paso 2: Iniciar Todo

**Ejecuta:**
```bash
INICIAR_TODO.bat
```

Este script:
- ✅ Inicia Django automáticamente
- ✅ Inicia ngrok automáticamente
- ✅ Te muestra la URL HTTPS

---

## 📱 Paso 3: Usar la URL de ngrok

ngrok mostrará algo como:
```
Forwarding   https://abc123.ngrok.io -> http://localhost:8000
```

**Usa esa URL en ambos dispositivos:**
- **Tu PC:** `https://abc123.ngrok.io`
- **Celular:** `https://abc123.ngrok.io`

---

## ✅ ¡Listo!

Ya puedes probar la videollamada desde ambos dispositivos con HTTPS.

---

## 🆘 Si algo falla

1. **ngrok no encontrado:**
   - Ejecuta: `INSTALAR_NGROK.bat`
   - O coloca `ngrok.exe` en la carpeta del proyecto

2. **Error "DisallowedHost":**
   - Ya está configurado automáticamente
   - Si persiste, verifica `.env`

3. **Django no inicia:**
   - Verifica que el puerto 8000 esté libre
   - Cierra otros programas que usen el puerto 8000

---

## 📝 Resumen Ultra Rápido

1. `INSTALAR_NGROK.bat` (solo la primera vez)
2. `INICIAR_TODO.bat` (cada vez que quieras probar)
3. Copia la URL HTTPS de ngrok
4. Úsala en ambos dispositivos
5. ¡Listo!

