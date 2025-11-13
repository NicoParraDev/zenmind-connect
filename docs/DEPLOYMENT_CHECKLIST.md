# ✅ Checklist de Despliegue a Producción

## 📋 Antes de Desplegar

### 1. Configuración del Proyecto
- [ ] `DEBUG=False` en variables de entorno
- [ ] `SECRET_KEY` nueva y segura generada
- [ ] `ALLOWED_HOSTS` configurado con tu dominio
- [ ] Base de datos cambiada de SQLite a PostgreSQL
- [ ] Redis configurado para Channels
- [ ] Variables de entorno documentadas

### 2. Archivos de Configuración
- [ ] `Procfile` creado (para Heroku/Railway)
- [ ] `runtime.txt` creado (versión de Python)
- [ ] `render.yaml` creado (si usas Render)
- [ ] `requirements.txt` actualizado (sin dependencias de desarrollo)
- [ ] `.gitignore` configurado correctamente

### 3. Base de Datos
- [ ] Backup de base de datos actual
- [ ] Migraciones aplicadas localmente
- [ ] Datos de prueba eliminados (opcional)
- [ ] Superusuario creado para producción

### 4. Archivos Estáticos y Media
- [ ] `collectstatic` funciona correctamente
- [ ] Archivos estáticos configurados para CDN
- [ ] Archivos media configurados para almacenamiento en la nube (S3, etc.)
- [ ] `STATIC_ROOT` y `MEDIA_ROOT` configurados

### 5. Seguridad
- [ ] HTTPS configurado
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] Headers de seguridad configurados
- [ ] Rate limiting activado

### 6. WebSockets (Channels)
- [ ] Redis configurado
- [ ] `CHANNEL_LAYERS` configurado con Redis
- [ ] `InMemoryChannelLayer` cambiado a `RedisChannelLayer`

### 7. Dependencias
- [ ] `pywin32` removido de `requirements.txt` (solo Windows)
- [ ] Dependencias de desarrollo removidas
- [ ] Versiones de dependencias fijadas

### 8. Logging y Monitoreo
- [ ] Sistema de logging configurado
- [ ] Sentry o similar configurado (opcional)
- [ ] Alertas configuradas

### 9. Email
- [ ] SMTP configurado
- [ ] Variables de entorno de email configuradas
- [ ] Email de prueba enviado

### 10. Agora (Videollamadas)
- [ ] Credenciales de Agora configuradas
- [ ] Variables de entorno de Agora configuradas

---

## 🚀 Durante el Despliegue

### 1. Plataforma
- [ ] Cuenta creada en la plataforma elegida
- [ ] Proyecto creado en la plataforma
- [ ] Repositorio conectado (GitHub/GitLab)

### 2. Servicios
- [ ] Base de datos PostgreSQL creada
- [ ] Redis creado (si es necesario)
- [ ] Storage configurado (S3, Azure Storage, etc.)

### 3. Variables de Entorno
- [ ] Todas las variables configuradas en la plataforma
- [ ] `SECRET_KEY` configurada
- [ ] Credenciales de base de datos configuradas
- [ ] Credenciales de email configuradas
- [ ] Credenciales de Agora configuradas

### 4. Build y Deploy
- [ ] Build exitoso
- [ ] Migraciones aplicadas automáticamente
- [ ] `collectstatic` ejecutado
- [ ] Aplicación iniciada correctamente

---

## ✅ Después del Despliegue

### 1. Verificación
- [ ] Aplicación accesible en la URL
- [ ] HTTPS funcionando
- [ ] Admin accesible
- [ ] Login funcionando
- [ ] Registro funcionando

### 2. Funcionalidades
- [ ] Sistema de reservas funcionando
- [ ] Blog/Posts funcionando
- [ ] Videollamadas funcionando (si aplica)
- [ ] WebSockets funcionando (si aplica)
- [ ] Archivos media subiendo correctamente

### 3. Base de Datos
- [ ] Datos migrados correctamente
- [ ] Superusuario puede hacer login
- [ ] Datos de prueba verificados

### 4. Performance
- [ ] Páginas cargan rápido
- [ ] Archivos estáticos servidos correctamente
- [ ] CDN funcionando (si aplica)

### 5. Seguridad
- [ ] HTTPS redirige correctamente
- [ ] Cookies seguras funcionando
- [ ] CSRF funcionando
- [ ] Headers de seguridad presentes

### 6. Monitoreo
- [ ] Logs accesibles
- [ ] Errores siendo registrados
- [ ] Alertas configuradas (si aplica)

---

## 🔧 Configuraciones Específicas

### Railway
- [ ] `Procfile` en la raíz
- [ ] `runtime.txt` en la raíz
- [ ] Variables de entorno configuradas
- [ ] PostgreSQL agregado desde marketplace
- [ ] Redis agregado desde marketplace

### Render
- [ ] `render.yaml` en la raíz (opcional)
- [ ] Variables de entorno configuradas
- [ ] PostgreSQL creado
- [ ] Redis creado (si necesario)

### Heroku
- [ ] `Procfile` en la raíz
- [ ] `runtime.txt` en la raíz
- [ ] Add-ons instalados (PostgreSQL, Redis)
- [ ] Variables de entorno configuradas con `heroku config:set`

### Azure
- [ ] `web.config` o Dockerfile
- [ ] App Service creado
- [ ] Azure Database para PostgreSQL creado
- [ ] Azure Cache para Redis creado
- [ ] Variables de entorno en App Settings

### AWS
- [ ] Elastic Beanstalk o EC2 configurado
- [ ] RDS (PostgreSQL) creado
- [ ] ElastiCache (Redis) creado
- [ ] S3 para storage configurado
- [ ] Variables de entorno configuradas

---

## 📝 Notas Finales

- ✅ Siempre haz backup antes de desplegar
- ✅ Prueba en un entorno de staging primero (si es posible)
- ✅ Monitorea los logs después del despliegue
- ✅ Verifica que todas las funcionalidades críticas funcionen
- ✅ Configura backups automáticos de la base de datos
- ✅ Documenta todas las configuraciones

---

**¡Buena suerte con tu despliegue! 🚀**

