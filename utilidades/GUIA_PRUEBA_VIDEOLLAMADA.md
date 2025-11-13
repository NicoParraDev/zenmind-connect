# 🎥 Guía para Probar Videollamada

## 🚀 Opción 1: Local (Sin ngrok) - Más Rápido

### Paso 1: Iniciar Django
```bash
# Desde la raíz del proyecto
python manage.py runserver
```

O usa el script:
```bash
scripts\REINICIAR_DJANGO.bat
```

### Paso 2: Abrir Navegadores

1. **Chrome Normal:**
   - Abre: `http://127.0.0.1:8000`
   - Inicia sesión con: `usuario` / `usuario123`

2. **Chrome Incógnito (Ctrl+Shift+N):**
   - Abre: `http://127.0.0.1:8000`
   - Inicia sesión con: `testuser` / `testuser123`

### Paso 3: Crear/Unirse a Sala

1. Desde Chrome normal (usuario):
   - Ve a tu perfil
   - Crea una nueva sala de videollamada
   - Copia el enlace de la sala

2. Desde Chrome incógnito (testuser):
   - Pega el enlace de la sala
   - O busca la opción "Unirse a sala"

---

## 🌐 Opción 2: Con ngrok (Para probar desde celular)

### Paso 1: Iniciar Todo
```bash
scripts\INICIAR_TODO_SIMPLE.bat
```

Esto iniciará:
- Django en una ventana
- Ngrok en otra ventana

### Paso 2: Obtener URL de ngrok

1. Ve a la ventana de ngrok
2. Copia la URL HTTPS (ejemplo: `https://abc123.ngrok-free.dev`)

### Paso 3: Abrir Navegadores

1. **Chrome Normal:**
   - Abre: `[URL de ngrok]`
   - Inicia sesión con: `usuario` / `usuario123`

2. **Chrome Incógnito:**
   - Abre: `[URL de ngrok]`
   - Inicia sesión con: `testuser` / `testuser123`

---

## ✅ Qué Verificar

- ✅ Ambos usuarios pueden ver su propia cámara
- ✅ Ambos usuarios pueden ver la cámara del otro
- ✅ El audio funciona (puede requerir activación manual)
- ✅ Los controles funcionan (mute, cámara on/off)

---

## 🔧 Si Hay Problemas

### No veo la cámara del otro usuario:
1. Verifica que ambos hayan permitido cámara/micrófono
2. Revisa la consola del navegador (F12)
3. Asegúrate de que ambos estén en la misma sala

### Error de permisos:
1. Ve a Configuración del navegador
2. Permisos → Cámara → Permitir
3. Permisos → Micrófono → Permitir

### Error de conexión:
1. Verifica que Django esté corriendo
2. Si usas ngrok, verifica que esté activo
3. Revisa que la URL sea correcta

---

## 💡 Tips

- **Modo local es más rápido** para pruebas rápidas
- **Ngrok es necesario** solo si quieres probar desde otro dispositivo
- **Chrome incógnito** es perfecto para simular dos usuarios diferentes
- **Permite siempre** cámara y micrófono cuando el navegador lo pida

