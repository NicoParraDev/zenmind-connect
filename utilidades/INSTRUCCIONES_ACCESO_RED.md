# 📱 Cómo acceder desde otro dispositivo

## Opción 1: Modificar .env (Recomendado)

1. **Edita tu archivo `.env`** y modifica la línea `ALLOWED_HOSTS`:
   ```
   ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83
   ```
   
   O si quieres permitir acceso desde cualquier IP en tu red local:
   ```
   ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83,192.168.1.*
   ```

2. **Ejecuta el servidor con acceso a red local**:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   
   O usa el script que creé:
   ```bash
   runserver_network.bat
   ```

3. **Desde otro dispositivo** (teléfono, tablet, otra PC en la misma red WiFi):
   - Abre el navegador
   - Ve a: `http://192.168.1.83:8000`
   - ¡Listo! Ya puedes probar la videollamada desde otro dispositivo

## Opción 2: Usar ngrok (Túnel público)

Si quieres probar desde internet (no solo red local):

1. **Instala ngrok**: https://ngrok.com/download

2. **Ejecuta Django normalmente**:
   ```bash
   python manage.py runserver
   ```

3. **En otra terminal, ejecuta ngrok**:
   ```bash
   ngrok http 8000
   ```

4. **Usa la URL que ngrok te da** (ej: `https://abc123.ngrok.io`) desde cualquier dispositivo con internet.

## Opción 3: Usar dos navegadores en la misma PC

Si no puedes usar otro dispositivo, puedes usar:
- **Chrome normal** + **Chrome en modo incógnito**
- **Chrome** + **Edge**
- **Firefox** + **Chrome**

Pero ten en cuenta que ambos intentarán usar la misma cámara/micrófono, lo que causa el error "Device in use".

## ⚠️ IMPORTANTE

- Asegúrate de que ambos dispositivos estén en la **misma red WiFi**
- Si tienes firewall, permite el puerto 8000
- La IP `192.168.1.83` puede cambiar si reinicias el router - verifica con `ipconfig` si no funciona

