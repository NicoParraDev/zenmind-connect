# 🔄 GitHub Actions - CI/CD Pipeline

**Fecha de Implementación**: 2025-01-11  
**Estado**: ✅ **CONFIGURADO**

---

## 📋 RESUMEN

Se ha configurado un pipeline completo de CI/CD usando GitHub Actions para automatizar:
- ✅ Testing automático
- ✅ Linting y calidad de código
- ✅ Escaneo de seguridad
- ✅ Build y verificación
- ✅ Deployment automático
- ✅ Análisis de código (CodeQL)

---

## 🎯 WORKFLOWS CONFIGURADOS

### 1. **CI Pipeline** (`.github/workflows/ci.yml`)

#### **Jobs Incluidos:**

##### **🧪 Test Job**
- ✅ Ejecuta tests en PostgreSQL
- ✅ Genera reporte de cobertura
- ✅ Sube cobertura a Codecov
- ✅ Ejecuta en Ubuntu Latest
- ✅ Python 3.10

##### **🔍 Lint Job**
- ✅ Flake8 para análisis de código
- ✅ Black para verificación de formato
- ✅ isort para verificación de imports
- ✅ Pylint para análisis estático

##### **🛡️ Security Job**
- ✅ Bandit para escaneo de seguridad Python
- ✅ Safety para verificación de dependencias vulnerables
- ✅ Genera reportes JSON

##### **🏗️ Build Job**
- ✅ Verifica que el proyecto compile
- ✅ Collect static files
- ✅ Verifica migraciones
- ✅ Solo se ejecuta si test, lint y security pasan

#### **Triggers:**
- Push a `main`, `master`, `develop`
- Pull Requests a `main`, `master`, `develop`

---

### 2. **Pre-Deployment Checks** (`.github/workflows/deploy.yml`)

#### **Jobs Incluidos:**

##### **✅ Pre-Deploy Job**
- ✅ Valida que `render.yaml` existe
- ✅ Valida que `requirements.txt` existe
- ✅ Verifica configuración básica
- ✅ Informa sobre deployment automático de Render

#### **⚠️ IMPORTANTE: Render Auto-Deploy**

**Render.com maneja el deployment automáticamente** cuando:
- ✅ El repositorio está conectado en Render dashboard
- ✅ `render.yaml` está presente en la raíz
- ✅ Se hace push a la rama conectada (main/master)

**NO necesitas un workflow de deploy separado** - Render lo hace automáticamente.

Este workflow solo valida que todo esté listo antes del deployment.

#### **Triggers:**
- Push a `main` o `master`
- Pull Requests a `main` o `master`

---

### 3. **CodeQL Analysis** (`.github/workflows/codeql.yml`)

#### **Características:**
- ✅ Análisis de código Python y JavaScript
- ✅ Detección de vulnerabilidades
- ✅ Ejecución semanal (domingos)
- ✅ Ejecución en PRs y pushes

#### **Triggers:**
- Push a `main`, `master`, `develop`
- Pull Requests
- Schedule: Domingos a las 00:00 UTC

---

## 🔧 CONFIGURACIÓN REQUERIDA

### **Secrets de GitHub**

Para que los workflows funcionen completamente, necesitas configurar estos secrets en GitHub:

1. **`SECRET_KEY`** (Opcional para CI)
   - Secret key de Django para tests
   - Si no está, usa un valor por defecto para CI

### **⚠️ NOTA IMPORTANTE: Render Auto-Deploy**

**NO necesitas secrets de Render** porque Render maneja el deployment automáticamente desde GitHub cuando:
- Conectas tu repositorio en Render Dashboard
- `render.yaml` está presente en la raíz del proyecto
- Render detecta cambios en la rama conectada

**Configuración en Render:**
1. Ve a Render Dashboard
2. Conecta tu repositorio de GitHub
3. Render usará automáticamente el `render.yaml` para configurar los servicios
4. Cada push a `main`/`master` desplegará automáticamente

### **Cómo Configurar Secrets:**

1. Ve a tu repositorio en GitHub
2. Settings > Secrets and variables > Actions
3. Click en "New repository secret"
4. Agrega cada secret con su valor

---

## 📊 ESTADO DE LOS WORKFLOWS

| Workflow | Estado | Descripción |
|----------|--------|-------------|
| **CI** | ✅ Configurado | Testing, linting, security, build |
| **Pre-Deploy** | ✅ Configurado | Validación antes de deployment (Render hace el deploy automáticamente) |
| **CodeQL** | ✅ Configurado | Análisis de seguridad de código |

---

## 🚀 USO

### **Ejecución Automática**

Los workflows se ejecutan automáticamente cuando:
- Haces push a las ramas principales
- Creas un Pull Request
- Creas un tag de versión (para deploy)

### **Ejecución Manual**

También puedes ejecutar workflows manualmente desde:
- GitHub > Actions > Seleccionar workflow > Run workflow

---

## 📈 MÉTRICAS Y REPORTES

### **Cobertura de Tests**
- Se genera automáticamente en cada CI run
- Se sube a Codecov (si está configurado)
- Ver en: Actions > Test Job > Coverage report

### **Security Reports**
- Bandit: `bandit-report.json`
- Safety: Reporte en consola
- CodeQL: En la pestaña Security del repositorio

### **Linting Reports**
- Flake8: Estadísticas en consola
- Black: Lista de archivos que necesitan formato
- isort: Lista de imports que necesitan orden

---

## ⚙️ PERSONALIZACIÓN

### **Modificar Triggers**

Edita los archivos `.github/workflows/*.yml` y modifica la sección `on:`:

```yaml
on:
  push:
    branches: [ main, tu-rama ]
  pull_request:
    branches: [ main ]
```

### **Agregar Más Tests**

En `ci.yml`, en el job `test`, agrega más comandos:

```yaml
- name: Run specific tests
  run: |
    python manage.py test core.tests.test_views
```

### **Cambiar Plataforma de Deployment**

Si no usas Render, modifica `deploy.yml`:

```yaml
- name: Deploy to Heroku
  uses: akhileshns/heroku-deploy@v3.12.12
  with:
    heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
    heroku_app_name: "tu-app"
```

---

## ✅ BENEFICIOS

1. **Calidad de Código**: Tests automáticos en cada push
2. **Seguridad**: Escaneo automático de vulnerabilidades
3. **Deployment**: Despliegue automático sin intervención manual
4. **Confianza**: Saber que el código funciona antes de mergear
5. **Historial**: Ver el historial de builds y deployments

---

## 🔍 VERIFICACIÓN

Para verificar que todo funciona:

1. Haz un push a `main` o `develop`
2. Ve a GitHub > Actions
3. Deberías ver los workflows ejecutándose
4. Revisa los resultados de cada job

---

## 📝 NOTAS

- Los workflows usan PostgreSQL para tests (más realista que SQLite)
- La cobertura se sube a Codecov (opcional, no bloquea el CI)
- El deployment solo se ejecuta en `main`/`master` o tags
- CodeQL se ejecuta semanalmente además de en PRs

---

**Última actualización**: 2025-01-11

