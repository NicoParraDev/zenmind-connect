# 🚀 Deployment en Render.com

**Fecha**: 2025-01-11  
**Estado**: ✅ **CONFIGURADO**

---

## 📋 RESUMEN

Render.com maneja el deployment automáticamente desde GitHub usando el archivo `render.yaml` como configuración de infraestructura como código.

---

## 🔧 CONFIGURACIÓN ACTUAL

### **Archivo `render.yaml`**

El archivo `render.yaml` en la raíz del proyecto define:

```yaml
services:
  - type: web
    name: zenmindconnect
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput
    startCommand: daphne -b 0.0.0.0 -p $PORT ZenMindConnect.asgi:application
    envVars:
      - key: SECRET_KEY
        sync: false
      - key: DEBUG
        value: False
      - key: ALLOWED_HOSTS
        sync: false
      - key: DB_ENGINE
        value: django.db.backends.postgresql
      # ... más variables

databases:
  - name: zenmindconnect-db
    databaseName: zenmindconnect
    user: zenmindconnect
```

---

## 🔄 CÓMO FUNCIONA EL AUTO-DEPLOY

### **1. Configuración Inicial en Render**

1. **Crear cuenta en Render.com**
2. **Conectar repositorio de GitHub:**
   - Dashboard > New > Blueprint
   - Seleccionar tu repositorio
   - Render detectará automáticamente `render.yaml`
3. **Render creará automáticamente:**
   - Servicio web (desde `services:`)
   - Base de datos PostgreSQL (desde `databases:`)
   - Variables de entorno (desde `envVars:`)

### **2. Deployment Automático**

Render despliega automáticamente cuando:
- ✅ Push a la rama conectada (main/master)
- ✅ `render.yaml` está presente
- ✅ Repositorio está conectado

**NO necesitas:**
- ❌ GitHub Actions para deploy
- ❌ Secrets de Render en GitHub
- ❌ Configuración manual

---

## 📊 FLUJO COMPLETO

```
┌─────────────────┐
│  Push a GitHub  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Actions  │
│   (CI Pipeline) │
│  - Tests        │
│  - Lint         │
│  - Security     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Render Detecta │
│  Cambios en     │
│  render.yaml    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Render Deploy  │
│  Automático     │
│  - Build        │
│  - Deploy       │
└─────────────────┘
```

---

## ⚙️ CONFIGURACIÓN DE VARIABLES DE ENTORNO

### **Variables que DEBES configurar en Render Dashboard:**

1. **`SECRET_KEY`**
   - Generar: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - Configurar en Render Dashboard > Environment

2. **`ALLOWED_HOSTS`**
   - Formato: `tu-dominio.onrender.com,www.tu-dominio.com`
   - Render proporciona el dominio automáticamente

3. **`EMAIL_HOST_USER`** (si usas email)
4. **`EMAIL_HOST_PASSWORD`** (si usas email)
5. **`CSRF_TRUSTED_ORIGINS`** (si tienes dominio personalizado)

### **Variables Automáticas de Render:**

Render configura automáticamente:
- ✅ `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (desde `databases:`)
- ✅ `PORT` (puerto del servicio web)

---

## 🔍 VERIFICACIÓN

### **Verificar que Render está conectado:**

1. Ve a Render Dashboard
2. Deberías ver:
   - ✅ Servicio web "zenmindconnect"
   - ✅ Base de datos "zenmindconnect-db"
   - ✅ Estado: "Live" o "Building"

### **Verificar deployment automático:**

1. Haz un push a `main`/`master`
2. Ve a Render Dashboard
3. Deberías ver:
   - ✅ "Deploy in progress"
   - ✅ Logs de build
   - ✅ Estado final: "Live"

---

## 🛠️ COMANDOS ÚTILES

### **Ver logs de deployment:**
- Render Dashboard > Tu servicio > Logs

### **Verificar variables de entorno:**
- Render Dashboard > Tu servicio > Environment

### **Reiniciar servicio:**
- Render Dashboard > Tu servicio > Manual Deploy > Clear build cache & deploy

---

## ⚠️ NOTAS IMPORTANTES

1. **`render.yaml` debe estar en la raíz** del repositorio
2. **Render usa `render.yaml` como Blueprint** - cualquier cambio requiere reconexión o actualización manual
3. **Variables con `sync: false`** deben configurarse manualmente en Render Dashboard
4. **El deployment automático** solo funciona si el repositorio está conectado en Render

---

## 🔄 RELACIÓN CON GITHUB ACTIONS

### **GitHub Actions (CI):**
- ✅ Ejecuta tests
- ✅ Linting
- ✅ Security scanning
- ✅ Build verification

### **Render (CD):**
- ✅ Deployment automático
- ✅ Usa `render.yaml` para configuración
- ✅ Gestiona infraestructura

**Ambos trabajan juntos:**
- GitHub Actions valida el código
- Render despliega automáticamente si el código pasa las validaciones

---

## 📝 ACTUALIZAR CONFIGURACIÓN

Si necesitas cambiar la configuración de Render:

1. **Edita `render.yaml`**
2. **Haz commit y push**
3. **En Render Dashboard:**
   - Ve a tu servicio
   - Settings > Update Blueprint
   - Render aplicará los cambios

---

**Última actualización**: 2025-01-11

