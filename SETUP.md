# 🚀 CHECKLIST PARA LEVANTAR EL PROYECTO

## ✅ PASOS OBLIGATORIOS

### 1. Crear archivo .env
```bash
# Copia env.example a .env
copy env.example .env
# Luego edita .env con tus valores reales
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar .env
Edita el archivo `.env` y completa:
- SECRET_KEY (generar uno nuevo)
- DB_PASSWORD (tu contraseña de Oracle)
- EMAIL_HOST_USER y EMAIL_HOST_PASSWORD (si usas emails)

### 4. Verificar base de datos Oracle
Asegúrate que Oracle esté corriendo y accesible en `127.0.0.1:1521/xe`

### 5. Aplicar migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear superusuario
```bash
python manage.py createsuperuser
```

### 7. Levantar servidor
```bash
python manage.py runserver
```

## ⚠️ PROBLEMAS COMUNES

- **Si falta python-decouple**: `pip install python-decouple`
- **Si falla Oracle**: Puedes cambiar temporalmente a SQLite en settings.py
- **Si falta el directorio logs**: Se crea automáticamente, pero si falla: `mkdir logs`

