# 📹 Configuración de Agora para Videollamadas

## ⚠️ Error Actual
Si ves el error **"Configuración de Agora no disponible"**, significa que necesitas configurar las credenciales de Agora en tu archivo `.env`.

## 🚀 Pasos para Configurar Agora

### 1. Crear cuenta en Agora (si no tienes una)

1. Ve a: **https://console.agora.io/**
2. Crea una cuenta gratuita (tiene un plan gratuito generoso)
3. Inicia sesión en la consola

### 2. Crear un Proyecto

1. En el dashboard de Agora, haz clic en **"Create Project"**
2. Ingresa un nombre para tu proyecto (ej: "ZenMindConnect")
3. Selecciona **"Video Call"** como tipo de proyecto
4. Haz clic en **"Submit"**

### 3. Obtener las Credenciales

Una vez creado el proyecto, verás:

- **App ID**: Un identificador único (ej: `a1b2c3d4e5f6g7h8i9j0`)
- **App Certificate**: Una cadena de caracteres (ej: `abc123def456ghi789jkl012mno345pqr678stu901vwx234yz`)

### 4. Configurar en ZenMindConnect

1. Abre el archivo `.env` en la raíz del proyecto
2. Busca las líneas:
   ```
   AGORA_APP_ID=your-agora-app-id
   AGORA_APP_CERTIFICATE=your-agora-app-certificate
   ```
3. Reemplaza con tus credenciales reales:
   ```
   AGORA_APP_ID=a1b2c3d4e5f6g7h8i9j0
   AGORA_APP_CERTIFICATE=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
   ```
4. **Guarda el archivo**
5. **Reinicia el servidor Django** (Ctrl+C y luego `python manage.py runserver`)

## ✅ Verificación

Después de configurar:

1. Recarga la página del lobby de videollamadas
2. Intenta crear una sala
3. Ya no deberías ver el error de configuración

## 📝 Notas Importantes

- **Nunca compartas** tus credenciales de Agora públicamente
- El archivo `.env` está en `.gitignore` por seguridad
- El plan gratuito de Agora incluye:
  - 10,000 minutos de video al mes
  - Hasta 100 usuarios simultáneos
  - Perfecto para desarrollo y uso moderado

## 🔗 Enlaces Útiles

- **Consola de Agora**: https://console.agora.io/
- **Documentación**: https://docs.agora.io/
- **Soporte**: https://www.agora.io/en/support/

## 🆘 Si Tienes Problemas

1. Verifica que las credenciales estén correctamente escritas (sin espacios extra)
2. Asegúrate de haber guardado el archivo `.env`
3. Reinicia el servidor Django completamente
4. Verifica que el archivo `.env` esté en la raíz del proyecto (mismo nivel que `manage.py`)

