# 📋 PASO A PASO: Acceder desde el Celular

## ✅ Paso 1: Detener el servidor actual (si está corriendo)

1. Ve a la terminal donde está corriendo Django
2. Presiona `Ctrl+C` para detenerlo
3. Espera a que se detenga completamente

---

## ✅ Paso 2: Ejecutar el script automático

**Opción A: Usar el script que creé**
```bash
INICIAR_SERVIDOR_RED.bat
```

**Opción B: Manualmente**
```bash
python manage.py runserver 0.0.0.0:8000
```

**IMPORTANTE:** Debe decir `0.0.0.0:8000` (no solo `8000` o `127.0.0.1:8000`)

---

## ✅ Paso 3: Verificar que está escuchando correctamente

Abre **otra terminal** (deja la del servidor corriendo) y ejecuta:

```bash
netstat -an | findstr ":8000"
```

**Debes ver:**
```
TCP    0.0.0.0:8000         0.0.0.0:0              LISTENING
```

**Si ves esto (INCORRECTO):**
```
TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING
```
Entonces el servidor NO está configurado correctamente. Detén y reinicia con `0.0.0.0:8000`.

---

## ✅ Paso 4: Probar desde tu PC primero

Antes de probar desde el celular, verifica que funciona desde tu PC:

1. Abre tu navegador en tu PC
2. Ve a: `http://192.168.1.83:8000`
3. Debe cargar la página normalmente

**Si NO funciona en tu PC:**
- Verifica que el servidor esté corriendo
- Verifica que esté escuchando en `0.0.0.0:8000` (no `127.0.0.1:8000`)

**Si SÍ funciona en tu PC pero NO en el celular:**
- El problema es la red WiFi (ver Paso 5)

---

## ✅ Paso 5: Verificar red WiFi del celular

**IMPORTANTE:** Tu PC y celular deben estar en la **misma red WiFi**.

1. En tu PC, verifica tu red WiFi:
   - Abre Configuración → Red e Internet → WiFi
   - Anota el nombre de la red WiFi

2. En tu celular:
   - Ve a Configuración → WiFi
   - Verifica que esté conectado a la **misma red WiFi** que tu PC
   - Si está usando **datos móviles**, cámbialo a WiFi

---

## ✅ Paso 6: Probar desde el celular

1. Abre el navegador en tu celular (Chrome, Safari, etc.)
2. En la barra de direcciones, escribe:
   ```
   http://192.168.1.83:8000
   ```
3. Presiona "Ir" o "Enter"

**Si carga la página:**
- ✅ ¡Funciona! Ya puedes probar la videollamada

**Si NO carga:**
- Verifica que el celular esté en la misma WiFi
- Verifica que el servidor esté corriendo
- Verifica que el firewall de Windows no esté bloqueando

---

## ✅ Paso 7: Si aún no funciona - Verificar Firewall

1. Abre "Firewall de Windows Defender" en tu PC
2. Ve a "Configuración avanzada"
3. Busca "Reglas de entrada"
4. Busca reglas para "Python" o el puerto 8000
5. Si no hay reglas, crea una nueva:
   - Permitir conexiones entrantes
   - Puerto: 8000
   - Protocolo: TCP

O temporalmente desactiva el firewall para probar.

---

## 🎯 Resumen Rápido

1. ✅ Detén servidor actual (Ctrl+C)
2. ✅ Ejecuta: `python manage.py runserver 0.0.0.0:8000`
3. ✅ Verifica con: `netstat -an | findstr ":8000"` (debe mostrar `0.0.0.0:8000`)
4. ✅ Prueba desde PC: `http://192.168.1.83:8000`
5. ✅ Verifica que celular esté en misma WiFi
6. ✅ Prueba desde celular: `http://192.168.1.83:8000`

---

## 🆘 Si Nada Funciona

Ejecuta estos comandos y compárteme los resultados:

```bash
# Verificar servidor
netstat -an | findstr ":8000"

# Verificar IP
ipconfig | findstr /i "IPv4"

# Verificar .env
type .env | findstr "ALLOWED_HOSTS"
```

