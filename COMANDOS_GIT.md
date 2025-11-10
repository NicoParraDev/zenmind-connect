# 📦 Comandos para Subir el Proyecto a GitHub

## 1. Verificar estado actual
```bash
git status
```

## 2. Agregar todos los archivos (excepto los ignorados en .gitignore)
```bash
git add .
```

## 3. Verificar qué se va a subir
```bash
git status
```

## 4. Hacer el commit inicial
```bash
git commit -m "Initial commit: ZenMindConnect 2.0 - Plataforma de bienestar mental con IA"
```

## 5. Conectar con el repositorio remoto (si ya lo creaste en GitHub)
```bash
git remote add origin https://github.com/NicoParraDev/ZenMindConnect.git
```

## 6. Verificar la conexión remota
```bash
git remote -v
```

## 7. Subir el proyecto a GitHub
```bash
git push -u origin master
```

O si tu rama principal se llama `main`:
```bash
git branch -M main
git push -u origin main
```

---

## ⚠️ Notas Importantes

- ✅ El archivo `.gitignore` está configurado para **NO subir**:
  - Videos (`.mp4`, `.avi`, etc.)
  - Base de datos (`db.sqlite3`)
  - Archivos de log
  - Variables de entorno (`.env`)
  - Archivos de Python compilados (`__pycache__`)
  - Media y staticfiles

- ✅ **SÍ se subirán**:
  - Todo el código fuente
  - Modelo de IA entrenado (`.h5` y `tokenizador.json`)
  - Templates y archivos estáticos (CSS, JS, imágenes)
  - Documentación en `docs/`
  - `requirements.txt`
  - `README.md` actualizado con el stack tecnológico

---

## 🔍 Verificar antes de subir

Ejecuta estos comandos para ver qué se va a subir:

```bash
# Ver archivos que se agregarán
git status

# Ver archivos que NO se subirán (ignorados)
git status --ignored
```

---

## 📝 Si necesitas actualizar después

```bash
git add .
git commit -m "Descripción de los cambios"
git push
```

