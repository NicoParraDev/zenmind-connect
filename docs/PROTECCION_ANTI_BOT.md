# 🛡️ PROTECCIÓN ANTI-BOT Y ANTI-SCRAPING - ZenMindConnect 2.0

## ✅ IMPLEMENTACIONES COMPLETADAS

### 1. **Middleware Anti-Bot** (`core/middleware.py`)

#### Características:
- ✅ **Detección de User-Agents de bots**: Detecta RocketBot, UiPath, Selenium, Scrapy, etc.
- ✅ **Detección de headers sospechosos**: Verifica headers faltantes comunes en bots
- ✅ **Detección de patrones de scraping**: 
  - Más de 30 requests por minuto por IP
  - Más de 20 rutas diferentes en 1 minuto
- ✅ **Verificación de JavaScript**: Requiere JavaScript activo para rutas críticas
- ✅ **Rate limiting avanzado**: Bloquea IPs con comportamiento sospechoso

#### Bots Detectados:
- RocketBot
- UiPath
- Selenium/WebDriver
- Scrapy
- BeautifulSoup
- Python requests
- curl/wget
- Y muchos más...

### 2. **Protección JavaScript** (`core/static/JS/zenmind_2.0_interactive.js`)

#### Características:
- ✅ **Token automático**: Se establece automáticamente en todos los formularios
- ✅ **Cookie de verificación**: Cookie `js_enabled=1` para verificación
- ✅ **Header HTTP**: Header `X-JS-Token: active` en todas las peticiones
- ✅ **Campo hidden**: Campo `js_token` en todos los formularios

### 3. **Configuración en Settings**

- ✅ Middleware agregado a `MIDDLEWARE` en `settings.py`
- ✅ Cache configurado para rate limiting

## 🔒 MECANISMOS DE PROTECCIÓN

### Nivel 1: Detección de User-Agent
```python
# Bloquea automáticamente si detecta:
- 'rocketbot', 'uipath', 'selenium', 'scrapy', etc.
- User-Agent muy corto (< 10 caracteres)
- Sin User-Agent
```

### Nivel 2: Detección de Headers
```python
# Verifica headers comunes de navegadores:
- HTTP_ACCEPT
- HTTP_ACCEPT_LANGUAGE
# Si faltan más de la mitad, es sospechoso
```

### Nivel 3: Patrones de Scraping
```python
# Detecta:
- > 30 requests/minuto por IP
- > 20 rutas diferentes en 1 minuto
```

### Nivel 4: Verificación JavaScript
```python
# Para rutas críticas requiere:
- Cookie: js_enabled=1
- Header: X-JS-Token: active
- Campo POST: js_token=active
```

### Nivel 5: Rate Limiting
```python
# Ya implementado anteriormente:
- 5 intentos de login por IP/usuario
- Ventana de 5 minutos
```

## 📊 RUTAS PROTEGIDAS

### Rutas que requieren JavaScript:
- `/sesion/` - Login
- `/registrar_usuario/` - Registro
- `/form_post/` - Crear post
- `/marcar_consulta/` - Reservar cita

### Rutas ignoradas (no se aplica protección):
- `/admin/` - Panel de administración
- `/static/` - Archivos estáticos
- `/media/` - Archivos de medios
- `/favicon.ico` - Favicon
- `/robots.txt` - Robots.txt
- `/sitemap.xml` - Sitemap

## 🚫 RESPUESTAS DE BLOQUEO

### Para requests AJAX:
```json
{
    "error": "Acceso denegado",
    "message": "Tu solicitud ha sido bloqueada por medidas de seguridad."
}
```

### Para navegadores:
Página HTML con mensaje de acceso denegado.

## 📝 LOGGING

Todos los intentos de bots se registran en los logs:
```python
logger.warning(
    f"Bot detectado - IP: {ip}, User-Agent: {ua}, Path: {path}"
)
```

## ⚙️ CONFIGURACIÓN

### Ajustar límites en `core/middleware.py`:

```python
# Cambiar límite de requests por minuto
if request_count > 30:  # Cambiar este número

# Cambiar límite de rutas diferentes
if len(paths) > 20:  # Cambiar este número

# Cambiar umbral de sospecha por falta de JS
if suspicious_count >= 10:  # Cambiar este número
```

## 🔧 MANTENIMIENTO

### Ver logs de bots bloqueados:
```bash
# En Windows
type logs\django.log | findstr "Bot detectado"

# En Linux/Mac
grep "Bot detectado" logs/django.log
```

### Limpiar cache de rate limiting:
```python
from django.core.cache import cache
cache.clear()  # Limpia todo el cache
```

## 🎯 EFECTIVIDAD

### Protegido contra:
- ✅ RocketBot
- ✅ UiPath
- ✅ Selenium/WebDriver
- ✅ Scrapy
- ✅ BeautifulSoup
- ✅ Python requests
- ✅ curl/wget
- ✅ Bots sin JavaScript
- ✅ Scrapers automatizados

### No afecta:
- ✅ Navegadores normales (Chrome, Firefox, Edge, Safari)
- ✅ Usuarios legítimos
- ✅ APIs legítimas con headers correctos

## 📈 PRÓXIMAS MEJORAS SUGERIDAS

1. **reCAPTCHA v3** (opcional): Para protección adicional
2. **Honeypot fields**: Campos ocultos en formularios
3. **Verificación de tiempo**: Tiempo mínimo para completar formularios
4. **Análisis de comportamiento**: Mouse movements, keystrokes, etc.
5. **IP whitelist/blacklist**: Listas de IPs permitidas/bloqueadas

---

**Última actualización**: 2025-01-10
**Estado**: ✅ Implementado y activo

