# 🔐 Configurar Autenticación de ngrok

## ❌ Error: Requiere cuenta verificada

ngrok ahora requiere una cuenta gratuita para usar.

---

## ✅ Solución: Crear cuenta y configurar authtoken

### Paso 1: Crear cuenta en ngrok

1. Ve a: https://dashboard.ngrok.com/signup
2. Regístrate con tu email (es gratis)
3. Verifica tu email

### Paso 2: Obtener tu authtoken

1. Después de registrarte, ve a: https://dashboard.ngrok.com/get-started/your-authtoken
2. Copia tu authtoken (algo como: `2abc123def456ghi789jkl012mno345pqr678stu901vwx234yz`)

### Paso 3: Configurar authtoken

Ejecuta este comando en CMD (reemplaza TU_AUTHTOKEN con el que copiaste):

```bash
C:\ngrok\ngrok.exe config add-authtoken TU_AUTHTOKEN
```

O si ngrok está en el PATH:

```bash
ngrok config add-authtoken TU_AUTHTOKEN
```

---

## 🚀 Después de configurar

Una vez configurado el authtoken, puedes usar ngrok normalmente:

```bash
C:\ngrok\ngrok.exe http 8000
```

---

## 📝 Resumen

1. Crear cuenta: https://dashboard.ngrok.com/signup
2. Obtener authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
3. Configurar: `ngrok config add-authtoken TU_AUTHTOKEN`
4. Usar: `ngrok http 8000`

