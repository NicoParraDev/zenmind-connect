# 🚀 Configuración de Render.com - Guía Completa

**Fecha**: 2025-01-11  
**Estado**: ✅ **CONFIGURADO**

---

## 📋 RESUMEN

El archivo `render.yaml` es la configuración de **Infraestructura como Código** para Render.com. Render lo usa automáticamente para crear y configurar todos los servicios necesarios.

---

## 📁 ARCHIVO `render.yaml`

### **Ubicación**: Raíz del proyecto

### **Función**:
- ✅ Define servicios web
- ✅ Define bases de datos
- ✅ Configura variables de entorno
- ✅ Especifica comandos de build y start

---

## 🔧 CONFIGURACIÓN ACTUAL

### **Servicio Web**

```yaml
services:
  - type: web
    name: zenmindconnect
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput
    startCommand: daphne -b 0.0.0.0 -p $PORT ZenMindConnect.asgi:application
```

**Características**:
- ✅ Usa Python
- ✅ Instala dependencias
- ✅ Recolecta archivos estáticos
- ✅ Inicia con Daphne (ASGI para WebSockets)

### **Base de Datos**

```yaml
databases:
  - name: zenmindconnect-db
    databaseName: zenmindconnect
    user: zenmindconnect
```

**Características**:
- ✅ PostgreSQL automático
- ✅ Variables de conexión inyectadas automáticamente

---

## 🔐 VARIABLES DE ENTORNO

### **Variables Automáticas (de Render)**

Estas se configuran automáticamente:
- ✅ `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (desde la BD)
- ✅ `PORT` (puerto del servicio web)

### **Variables que DEBES Configurar Manualmente**

En Render Dashboard > Tu Servicio > Environment, agrega:

#### **1. Django Core**
- **`SECRET_KEY`**: Generar con:
  ```bash
  python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

- **`ALLOWED_HOSTS`**: 
  - Formato: `tu-app.onrender.com,www.tu-dominio.com`
  - Render proporciona el dominio automáticamente

- **`CSRF_TRUSTED_ORIGINS`**:
  - Formato: `https://tu-app.onrender.com,https://www.tu-dominio.com`

#### **2. Email (Opcional pero recomendado)**
- **`EMAIL_HOST_USER`**: Tu email (ej: `tu-email@hotmail.com`)
- **`EMAIL_HOST_PASSWORD`**: Contraseña del email

#### **3. Agora Video Call (Obligatorio para videollamadas)**
- **`AGORA_APP_ID`**: Obtener en https://console.agora.io/
- **`AGORA_APP_CERTIFICATE`**: Obtener en https://console.agora.io/

#### **4. OpenAI (Obligatorio para chatbot)**
- **`OPENAI_API_KEY`**: Obtener en https://platform.openai.com/api-keys

---

## 🚀 CÓMO USAR `render.yaml`

### **Opción 1: Blueprint (Recomendado - Primera vez)**

1. **Ve a Render Dashboard**
2. **New > Blueprint**
3. **Conecta tu repositorio de GitHub**
4. **Render detectará automáticamente `render.yaml`**
5. **Render creará:**
   - ✅ Servicio web
   - ✅ Base de datos PostgreSQL
   - ✅ Variables de entorno (las que tienen `sync: false` debes agregarlas manualmente)

### **Opción 2: Servicio Existente**

Si ya tienes un servicio en Render:

1. **Ve a tu servicio en Render Dashboard**
2. **Settings > Update Blueprint**
3. **Render aplicará los cambios de `render.yaml`**

---

## ⚙️ CONFIGURACIÓN PASO A PASO

### **Paso 1: Conectar Repositorio**

1. Render Dashboard > New > Blueprint
2. Selecciona tu repositorio de GitHub
3. Render detectará `render.yaml` automáticamente

### **Paso 2: Configurar Variables de Entorno**

1. Ve a tu servicio web en Render Dashboard
2. Settings > Environment
3. Agrega las variables con `sync: false`:
   - `SECRET_KEY`
   - `ALLOWED_HOSTS`
   - `EMAIL_HOST_USER`
   - `EMAIL_HOST_PASSWORD`
   - `AGORA_APP_ID`
   - `AGORA_APP_CERTIFICATE`
   - `OPENAI_API_KEY`
   - `CSRF_TRUSTED_ORIGINS`

### **Paso 3: Ejecutar Migraciones**

Las migraciones se ejecutan automáticamente en el primer deploy, pero puedes ejecutarlas manualmente:

1. Render Dashboard > Tu Servicio > Shell
2. Ejecuta:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

### **Paso 4: Verificar Deployment**

1. Ve a tu servicio en Render Dashboard
2. Deberías ver:
   - ✅ Estado: "Live"
   - ✅ URL: `https://tu-app.onrender.com`
   - ✅ Logs sin errores

---

## 🔄 DEPLOYMENT AUTOMÁTICO

### **Cómo Funciona**

1. **Haces push a `main`/`master`**
2. **Render detecta el cambio automáticamente**
3. **Render ejecuta:**
   - `buildCommand`: Instala dependencias y recolecta estáticos
   - Migraciones (si están configuradas)
   - `startCommand`: Inicia el servidor

### **Ver Logs de Deployment**

1. Render Dashboard > Tu Servicio > Logs
2. Verás:
   - Build logs
   - Runtime logs
   - Errores (si los hay)

---

## ⚠️ NOTAS IMPORTANTES

### **1. Variables con `sync: false`**

Estas variables **NO** se sincronizan desde `render.yaml` y debes configurarlas manualmente en Render Dashboard:
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `AGORA_APP_ID`
- `AGORA_APP_CERTIFICATE`
- `OPENAI_API_KEY`
- `CSRF_TRUSTED_ORIGINS`

### **2. Migraciones**

Render ejecuta migraciones automáticamente en el primer deploy. Para migraciones posteriores:
- Opción 1: Agregar `releaseCommand` en `render.yaml` (se ejecuta antes de cada deploy)
- Opción 2: Ejecutar manualmente desde Shell

### **3. Archivos Estáticos**

- `collectstatic` se ejecuta en `buildCommand`
- Los archivos estáticos se sirven desde `STATIC_ROOT`
- Render maneja esto automáticamente

### **4. WebSockets**

- ✅ Daphne está configurado correctamente
- ✅ Render soporta WebSockets
- ✅ No se necesita configuración adicional

---

## 🔍 TROUBLESHOOTING

### **Problema: Deployment falla**

**Solución**:
1. Revisa los logs en Render Dashboard
2. Verifica que todas las variables con `sync: false` estén configuradas
3. Verifica que `SECRET_KEY` esté configurado

### **Problema: Base de datos no conecta**

**Solución**:
1. Verifica que la BD esté creada
2. Verifica que las variables `DB_*` estén configuradas (se configuran automáticamente)
3. Revisa los logs de conexión

### **Problema: WebSockets no funcionan**

**Solución**:
1. Verifica que `startCommand` use `daphne` (no `gunicorn`)
2. Verifica que `ASGI_APPLICATION` esté configurado en `settings.py`
3. Revisa los logs de WebSocket

---

## 📊 ESTRUCTURA DEL `render.yaml`

```yaml
services:          # Servicios web/workers
  - type: web      # Tipo de servicio
    name: ...      # Nombre del servicio
    env: python    # Entorno
    buildCommand:  # Comando de build
    startCommand: # Comando de inicio
    envVars:      # Variables de entorno
      - key: ...   # Nombre de variable
        value: ... # Valor (o fromDatabase para BD)

databases:         # Bases de datos
  - name: ...     # Nombre de la BD
    databaseName: # Nombre de la base de datos
    user: ...     # Usuario
```

---

## ✅ CHECKLIST DE CONFIGURACIÓN

Antes de hacer deploy, verifica:

- [ ] `render.yaml` está en la raíz del proyecto
- [ ] Repositorio está conectado en Render Dashboard
- [ ] `SECRET_KEY` está configurado en Render Dashboard
- [ ] `ALLOWED_HOSTS` está configurado (con el dominio de Render)
- [ ] `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` configurados (si usas email)
- [ ] `AGORA_APP_ID` y `AGORA_APP_CERTIFICATE` configurados (si usas videollamadas)
- [ ] `OPENAI_API_KEY` configurado (si usas chatbot)
- [ ] `CSRF_TRUSTED_ORIGINS` configurado
- [ ] Migraciones ejecutadas
- [ ] Superusuario creado

---

## 🎯 CONCLUSIÓN

El archivo `render.yaml` es tu configuración de infraestructura. Render lo usa automáticamente para:
- ✅ Crear servicios
- ✅ Crear bases de datos
- ✅ Configurar variables de entorno (las automáticas)
- ✅ Hacer deployment automático

**Solo necesitas**:
1. Mantener `render.yaml` actualizado
2. Configurar variables con `sync: false` en Render Dashboard
3. Hacer push a GitHub

**Render hace el resto automáticamente** 🚀

---

**Última actualización**: 2025-01-11

