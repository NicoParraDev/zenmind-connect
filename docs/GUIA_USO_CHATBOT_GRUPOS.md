# 🚀 Guía de Uso: Chatbot IA + Grupos de Apoyo

## ✅ Estado: Todo Listo para Usar

Tu API key de OpenAI está configurada y el sistema está listo para funcionar.

---

## 🤖 CÓMO USAR EL CHATBOT

### **Acceso:**
1. Inicia sesión en ZenMindConnect
2. Ve a: **http://localhost:8000/chatbot/**
3. ¡Comienza a chatear!

### **Características:**
- ✅ Chat en tiempo real con IA
- ✅ Detección automática de crisis
- ✅ Recomendaciones de psicólogos
- ✅ Historial de conversaciones

### **Ejemplos de Preguntas:**
- "¿Qué puedo hacer para reducir mi ansiedad?"
- "Me siento muy estresado últimamente"
- "¿Cuándo debería consultar con un psicólogo?"
- "Necesito ayuda con mi autoestima"

### **Detección de Crisis:**
Si el chatbot detecta palabras de crisis, mostrará:
- ⚠️ Alerta de crisis
- 📞 Números de emergencia
- 👨‍⚕️ Recomendación de psicólogo

---

## 👥 CÓMO USAR GRUPOS DE APOYO

### **Acceso:**
1. Inicia sesión en ZenMindConnect
2. Ve a: **http://localhost:8000/grupos/**

### **Crear un Grupo:**
1. Click en "Crear Grupo"
2. Completa el formulario:
   - Nombre del grupo
   - Descripción
   - Tema (ansiedad, depresión, etc.)
   - Máximo de miembros
3. Click en "Crear Grupo"

### **Unirse a un Grupo:**
1. Ve a la lista de grupos
2. Click en "Ver Detalles" del grupo que te interese
3. Click en "Unirse al Grupo"

### **Sesiones Grupales:**
1. Una vez que eres miembro, puedes acceder a la sala
2. Click en "Entrar a Sala" para videollamada grupal
3. Usa el chat grupal para comunicarte

### **Temas Disponibles:**
- 😰 Ansiedad
- 😔 Depresión
- 💔 Duelo y Pérdida
- 😓 Estrés
- 💪 Autoestima
- 💑 Relaciones
- 🚫 Adicciones
- 🩹 Trauma
- 📌 Otro

---

## 🔧 VERIFICACIÓN RÁPIDA

### **1. Verificar que el servidor esté corriendo:**
```bash
python manage.py runserver
```

### **2. Probar el chatbot:**
- Ve a: http://localhost:8000/chatbot/
- Escribe un mensaje de prueba
- Verifica que recibas respuesta

### **3. Probar grupos:**
- Ve a: http://localhost:8000/grupos/
- Crea un grupo de prueba
- Únete a él

---

## ⚠️ TROUBLESHOOTING

### **Error: "OpenAI library no instalada"**
```bash
pip install openai==1.3.0
```

### **Error: "OPENAI_API_KEY no configurada"**
- Verifica que el archivo `.env` tenga:
  ```
  OPENAI_API_KEY=tu-api-key-aqui
  ```
- Reinicia el servidor después de agregar la key

### **Error: "No module named 'openai'"**
```bash
pip install -r requirements.txt
```

### **El chatbot no responde:**
- Verifica tu conexión a internet
- Verifica que tu API key sea válida
- Revisa los logs del servidor para ver errores

---

## 📊 ADMINISTRACIÓN

### **Ver Conversaciones del Chatbot:**
- Admin: http://localhost:8000/admin/core/chatconversation/
- Ver mensajes: http://localhost:8000/admin/core/chatmessagebot/

### **Ver Grupos de Apoyo:**
- Admin: http://localhost:8000/admin/core/grupoapoyo/
- Ver miembros: http://localhost:8000/admin/core/miembrogrupo/

---

## 💡 CONSEJOS

1. **Chatbot:**
   - Sé específico en tus preguntas
   - El chatbot es para información general, no reemplaza a un profesional
   - Si detecta crisis, sigue las recomendaciones

2. **Grupos:**
   - Únete a grupos relevantes a tus necesidades
   - Participa activamente en las sesiones
   - Comparte recursos útiles con el grupo

3. **Seguridad:**
   - No compartas información personal sensible en grupos públicos
   - Reporta contenido inapropiado
   - Respeta las reglas de cada grupo

---

## 🎉 ¡Todo Listo!

Tu sistema está completamente funcional. ¡Disfruta de las nuevas funcionalidades!

**Rutas principales:**
- Chatbot: `/chatbot/`
- Grupos: `/grupos/`
- Crear Grupo: `/grupos/crear/`

