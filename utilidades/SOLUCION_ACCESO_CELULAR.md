# 🔧 Solución: No puedo acceder desde el celular

## ❌ Problema Detectado

El servidor está corriendo solo en `127.0.0.1:8000` (localhost), por eso tu celular no puede acceder.

## ✅ Solución Paso a Paso

### Paso 1: Detener el servidor actual
Presiona `Ctrl+C` en la terminal donde está corriendo Django.

### Paso 2: Verificar/Configurar ALLOWED_HOSTS

**Opción A: Si tienes archivo `.env`**
Edita `.env` y agrega/modifica:
```
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83
```

**Opción B: Si NO tienes archivo `.env`**
Crea el archivo `.env` en la raíz del proyecto con:
```
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.83
DEBUG=True
SECRET_KEY=tu-secret-key-aqui
```

### Paso 3: Reiniciar el servidor CORRECTAMENTE

**IMPORTANTE:** Debes usar `0.0.0.0:8000` (no solo `8000` o `127.0.0.1:8000`):

```bash
python manage.py runserver 0.0.0.0:8000
```

O usa el script:
```bash
runserver_network.bat
```

### Paso 4: Verificar que está escuchando correctamente

Ejecuta en otra terminal:
```bash
netstat -an | findstr ":8000"
```

Deberías ver algo como:
```
TCP    0.0.0.0:8000         0.0.0.0:0              LISTENING
```

Si ves `127.0.0.1:8000` en lugar de `0.0.0.0:8000`, el servidor NO está configurado correctamente.

### Paso 5: Verificar desde tu PC

Primero prueba desde tu PC:
- `http://127.0.0.1:8000` - Debe funcionar
- `http://192.168.1.83:8000` - También debe funcionar

Si ambos funcionan en tu PC, entonces desde el celular también debería funcionar.

### Paso 6: Verificar red WiFi

- ✅ Tu PC y celular deben estar en la **misma red WiFi**
- ✅ Verifica que el celular esté conectado a la misma WiFi que tu PC
- ✅ Si usas datos móviles en el celular, NO funcionará

### Paso 7: Verificar firewall

Si aún no funciona:
1. Abre "Firewall de Windows Defender"
2. Permite Python a través del firewall
3. O temporalmente desactiva el firewall para probar

## 🧪 Prueba Rápida

1. Desde tu PC, abre: `http://192.168.1.83:8000`
   - Si funciona → El problema es la red del celular
   - Si NO funciona → El servidor no está configurado correctamente

2. Desde el celular, verifica que esté en la misma WiFi:
   - Configuración → WiFi → Debe estar conectado a la misma red que tu PC

## 📱 URLs para Probar

- **Desde tu PC:** `http://localhost:8000` o `http://127.0.0.1:8000`
- **Desde tu PC (IP local):** `http://192.168.1.83:8000`
- **Desde celular:** `http://192.168.1.83:8000`

Si la URL con IP local funciona en tu PC pero no en el celular, el problema es la red WiFi.

