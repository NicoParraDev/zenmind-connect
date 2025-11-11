# 🎯 PLAN DE INTEGRACIÓN: Chat + Videollamada en ZenMindConnect

**Fecha**: 2025-01-10  
**Objetivo**: Integrar Chat Calmind + VideoCall Calmind en una sola funcionalidad  
**Requisito**: NO perder funcionalidad existente, especialmente audios y grabaciones

---

## ✅ ANÁLISIS DE VIABILIDAD

### **¿ES POSIBLE? SÍ, TOTALMENTE** ✅

**Razones**:
1. ✅ Ambos proyectos usan Django (compatible)
2. ✅ Los audios están en archivos estáticos (NO se perderán)
3. ✅ Las grabaciones usan MediaRecorder (se mantiene)
4. ✅ VideoCall ya tiene botón "Ver chat" (línea 102-104 de room.html) - solo falta implementarlo
5. ✅ Ambos usan el concepto de "Room/Sala" (compatible)
6. ✅ Se pueden combinar en una sola interfaz

---

## 📊 ESTADO ACTUAL DE CADA PROYECTO

### **VideoCall Calmind - Funcionalidades a PRESERVAR**

#### ✅ **Sistema de Videollamadas**
- Agora SDK 4.8.0 integrado
- Video/audio en tiempo real
- Compartir pantalla
- Grabación de video/audio (MediaRecorder)
- Controles de micrófono/cámara
- Sistema de miembros (RoomMember)

#### ✅ **Audios/Notificaciones (8 archivos)**
```
static/music/
├── mixkit-light-button-2580.wav          ✅ PRESERVAR
├── mixkit-long-pop-2358.wav              ✅ PRESERVAR
├── mixkit-positive-notification-951.wav   ✅ PRESERVAR
├── mixkit-sci-fi-reject-notification-896.mp3  ✅ PRESERVAR
├── mixkit-software-interface-back-2575.mp3    ✅ PRESERVAR
├── mixkit-software-interface-remove-2576.mp3  ✅ PRESERVAR
├── pause record.wav                       ✅ PRESERVAR
└── start record.wav                       ✅ PRESERVAR
```

#### ✅ **Funcionalidades UI**
- Menú lateral con opciones
- Reloj en tiempo real
- Notificaciones SweetAlert2
- Fullscreen
- Modales de grabación
- Estilos CSS personalizados

### **Chat Calmind - Funcionalidades a INTEGRAR**

#### ✅ **Sistema de Chat**
- Modelos: `Room`, `Message`
- Vistas: `send()`, `getMessages()`
- Interfaz de chat básica
- Polling HTTP (mejorable pero funcional)

---

## 🎨 DISEÑO DE INTEGRACIÓN

### **Arquitectura Propuesta**

```
┌─────────────────────────────────────────┐
│     SALA DE VIDELLAMADA + CHAT          │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────┐  ┌───────────┐  │
│  │                  │  │           │  │
│  │  VIDEOS         │  │   CHAT    │  │
│  │  (Agora SDK)    │  │  (Panel   │  │
│  │                  │  │  Lateral) │  │
│  │  - Video local  │  │           │  │
│  │  - Videos remotos│  │  - Mensajes│  │
│  │  - Controles    │  │  - Enviar  │  │
│  │                  │  │  - Historial│ │
│  └──────────────────┘  └───────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  CONTROLES (mic, cam, share, etc) │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### **Flujo de Usuario**

1. Usuario entra a sala de videollamada (como ahora)
2. Se une a videollamada (Agora)
3. **NUEVO**: Panel de chat se abre automáticamente o con botón "Ver chat"
4. Puede chatear mientras está en videollamada
5. Los mensajes se guardan en BD (modelo Message)
6. Todo funciona simultáneamente

---

## 🔧 PLAN DE IMPLEMENTACIÓN

### **FASE 1: Preparación y Seguridad** (2-3 horas)

#### 1.1 Mover Credenciales a Variables de Entorno
```python
# En .env
AGORA_APP_ID=tu_app_id
AGORA_APP_CERTIFICATE=tu_certificate
```

#### 1.2 Integrar con Autenticación de ZenMindConnect
- Usar `@login_required` en todas las vistas
- Conectar con modelo `Persona` existente
- Usar `request.user` en lugar de nombres hardcodeados

#### 1.3 Mejorar Seguridad
- Remover `@csrf_exempt` o proteger adecuadamente
- Validar todas las entradas
- Configurar `ALLOWED_HOSTS` correctamente

### **FASE 2: Integración de Modelos** (3-4 horas)

#### 2.1 Unificar Modelos de Sala
```python
# Opción A: Usar RoomMember de VideoCall como base
# Opción B: Crear nuevo modelo unificado

class VideoCallRoom(models.Model):
    name = models.CharField(max_length=200, unique=True)
    created_by = models.ForeignKey(Persona, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    # Relacionar con Agenda de ZenMindConnect
    agenda = models.ForeignKey(Agenda, on_delete=models.SET_NULL, null=True)
    
class RoomMember(models.Model):
    # Mantener como está pero con ForeignKey a Persona
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    room = models.ForeignKey(VideoCallRoom, on_delete=models.CASCADE)
    uid = models.CharField(max_length=1000)
    joined_at = models.DateTimeField(auto_now_add=True)
    insession = models.BooleanField(default=True)

class ChatMessage(models.Model):
    # Mejorar modelo de Message
    room = models.ForeignKey(VideoCallRoom, on_delete=models.CASCADE)
    author = models.ForeignKey(Persona, on_delete=models.CASCADE)
    message = models.TextField(max_length=5000)  # Más razonable
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', 'created_at']),
        ]
```

#### 2.2 Migraciones
- Crear migraciones para nuevos modelos
- Migrar datos existentes si es necesario

### **FASE 3: Integración de Vistas** (4-5 horas)

#### 3.1 Crear Vista Unificada de Sala
```python
# core/videocall/views.py

@login_required
def video_call_room(request, room_name):
    """
    Vista unificada que combina videollamada + chat
    """
    try:
        # Obtener o crear sala
        room = VideoCallRoom.objects.get_or_create(
            name=room_name,
            defaults={'created_by': request.user.persona}
        )[0]
        
        # Obtener mensajes del chat
        messages = ChatMessage.objects.filter(room=room)[:50]
        
        # Obtener miembros en la sala
        members = RoomMember.objects.filter(room=room, insession=True)
        
        return render(request, 'core/videocall_room.html', {
            'room': room,
            'messages': messages,
            'members': members,
            'user': request.user,
        })
    except Exception as e:
        logger.error(f"Error en video_call_room: {e}")
        return redirect('index')
```

#### 3.2 Endpoints de Chat
```python
@login_required
@require_http_methods(["POST"])
def send_chat_message(request):
    """Enviar mensaje de chat"""
    data = json.loads(request.body)
    room_name = data.get('room_name')
    message_text = data.get('message')
    
    # Validar
    if not room_name or not message_text:
        return JsonResponse({'error': 'Datos inválidos'}, status=400)
    
    try:
        room = VideoCallRoom.objects.get(name=room_name)
        message = ChatMessage.objects.create(
            room=room,
            author=request.user.persona,
            message=message_text
        )
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'created_at': message.created_at.isoformat()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_chat_messages(request, room_name):
    """Obtener mensajes del chat"""
    try:
        room = VideoCallRoom.objects.get(name=room_name)
        messages = ChatMessage.objects.filter(room=room).order_by('created_at')
        
        messages_data = [{
            'id': msg.id,
            'author': msg.author.nombre + ' ' + msg.author.apellido,
            'message': msg.message,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]
        
        return JsonResponse({'messages': messages_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

#### 3.3 Mantener Endpoints de VideoCall
- `getToken()` - Mantener como está (mejorar seguridad)
- `createMember()` - Mejorar para usar Persona
- `getMember()` - Mantener
- `deleteMember()` - Mantener

### **FASE 4: Interfaz Unificada** (5-6 horas)

#### 4.1 Template Principal
```html
<!-- core/templates/core/videocall_room.html -->
{% extends 'core/base.html' %}
{% load static %}

{% block content %}
<div class="videocall-container">
    <!-- Panel de Videos (izquierda) -->
    <div class="video-panel">
        <!-- Videos de Agora SDK -->
        <section id="video-streams"></section>
        
        <!-- Controles -->
        <section id="controls-wrapper">
            <!-- Botones existentes (mic, cam, share, etc) -->
        </section>
    </div>
    
    <!-- Panel de Chat (derecha) - NUEVO -->
    <div class="chat-panel" id="chat-panel">
        <div class="chat-header">
            <h3>💬 Chat de la Sala</h3>
            <button onclick="toggleChat()">✕</button>
        </div>
        
        <div class="chat-messages" id="chat-messages">
            <!-- Mensajes se cargan aquí -->
        </div>
        
        <div class="chat-input">
            <input type="text" id="chat-input-field" placeholder="Escribe un mensaje...">
            <button onclick="sendChatMessage()">Enviar</button>
        </div>
    </div>
</div>

<!-- Scripts de Agora (mantener) -->
<script src="{% static 'assets/AgoraRTC_N-4.8.0.js' %}"></script>
<script src="{% static 'js/streams.js' %}"></script>

<!-- Scripts de Chat (NUEVO) -->
<script src="{% static 'js/videocall_chat.js' %}"></script>

<!-- Audios (PRESERVAR TODOS) -->
<audio id="audio" src="{% static 'music/mixkit-sci-fi-reject-notification-896.mp3' %}"></audio>
<audio id="audio2" src="{% static 'music/mixkit-positive-notification-951.wav' %}"></audio>
<!-- ... todos los demás audios ... -->
{% endblock %}
```

#### 4.2 JavaScript para Chat
```javascript
// static/js/videocall_chat.js

const CHAT_ROOM = sessionStorage.getItem('room');
const CHAT_USER = sessionStorage.getItem('name');

// Cargar mensajes iniciales
function loadChatMessages() {
    fetch(`/videocall/get_messages/${CHAT_ROOM}/`)
        .then(response => response.json())
        .then(data => {
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = '';
            
            data.messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'chat-message';
                messageDiv.innerHTML = `
                    <strong>${msg.author}:</strong>
                    <span>${msg.message}</span>
                    <small>${new Date(msg.created_at).toLocaleTimeString()}</small>
                `;
                messagesContainer.appendChild(messageDiv);
            });
            
            // Scroll al final
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        })
        .catch(error => console.error('Error cargando mensajes:', error));
}

// Enviar mensaje
function sendChatMessage() {
    const input = document.getElementById('chat-input-field');
    const message = input.value.trim();
    
    if (!message) return;
    
    fetch('/videocall/send_message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            room_name: CHAT_ROOM,
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            input.value = '';
            loadChatMessages(); // Recargar mensajes
        }
    })
    .catch(error => console.error('Error enviando mensaje:', error));
}

// Polling para nuevos mensajes (mejorable con WebSockets después)
setInterval(loadChatMessages, 2000); // Cada 2 segundos

// Cargar mensajes al iniciar
loadChatMessages();
```

#### 4.3 CSS para Panel de Chat
```css
/* Agregar a static/styles/videocall.css */

.videocall-container {
    display: flex;
    height: 100vh;
}

.video-panel {
    flex: 2;
    display: flex;
    flex-direction: column;
}

.chat-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-left: 2px solid #ddd;
    background: #f9f9f9;
}

.chat-header {
    padding: 15px;
    background: var(--primary-color);
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 15px;
}

.chat-message {
    margin-bottom: 15px;
    padding: 10px;
    background: white;
    border-radius: 8px;
}

.chat-input {
    padding: 15px;
    display: flex;
    gap: 10px;
    border-top: 1px solid #ddd;
}

.chat-input input {
    flex: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
}
```

### **FASE 5: Integración con Sistema de Reservas** (2-3 horas)

#### 5.1 Conectar con Agenda
```python
# Cuando se confirma una cita, crear sala automáticamente
def crear_sala_desde_cita(agenda, horario_agenda):
    """Crear sala de videollamada automáticamente al confirmar cita"""
    room_name = f"CONSULTA-{agenda.psicologo.id}-{horario_agenda.id}"
    
    room = VideoCallRoom.objects.create(
        name=room_name,
        created_by=horario_agenda.reservado_por,
        agenda=agenda
    )
    
    # Enviar notificación con link a la sala
    # ...
    
    return room
```

#### 5.2 Agregar Botón en Comprobante de Reserva
```html
<!-- En comprobante_reserva.html -->
<a href="{% url 'videocall_room' room_name=room_name %}" class="btn btn-primary">
    🎥 Iniciar Videollamada
</a>
```

### **FASE 6: Mejoras y Optimizaciones** (3-4 horas)

#### 6.1 Mejorar Polling a WebSockets (Opcional)
- Implementar Django Channels
- Chat en tiempo real sin polling
- Mejor experiencia de usuario

#### 6.2 Notificaciones de Chat
- Sonido cuando llega mensaje nuevo
- Badge con contador de mensajes no leídos
- Integrar con sistema de notificaciones existente

#### 6.3 Persistencia de Mensajes
- Guardar historial completo
- Permitir descargar historial
- Búsqueda en mensajes

---

## 📋 CHECKLIST DE INTEGRACIÓN

### **Preparación**
- [ ] Mover credenciales Agora a `.env`
- [ ] Integrar autenticación con ZenMindConnect
- [ ] Mejorar seguridad (remover @csrf_exempt, validaciones)
- [ ] Backup de datos existentes

### **Modelos**
- [ ] Crear modelos unificados
- [ ] Migrar datos existentes
- [ ] Conectar con modelo Persona
- [ ] Conectar con modelo Agenda

### **Backend**
- [ ] Crear vistas unificadas
- [ ] Endpoints de chat
- [ ] Mantener endpoints de videollamada
- [ ] Integrar con sistema de reservas

### **Frontend**
- [ ] Template unificado
- [ ] Panel de chat en interfaz
- [ ] JavaScript para chat
- [ ] CSS para layout
- [ ] Preservar todos los audios
- [ ] Preservar funcionalidad de grabación

### **Testing**
- [ ] Probar videollamada + chat simultáneamente
- [ ] Probar grabación con chat abierto
- [ ] Probar audios funcionando
- [ ] Probar integración con reservas

---

## 🎯 RESULTADO FINAL

### **Funcionalidades Integradas**

✅ **Videollamada Completa**
- Video/audio en tiempo real (Agora)
- Compartir pantalla
- Controles de micrófono/cámara
- Grabación de video/audio
- Sistema de miembros

✅ **Chat Integrado**
- Mensajería en tiempo real
- Historial de mensajes
- Panel lateral en videollamada
- Sincronizado con sala

✅ **Audios Preservados**
- Todos los 8 archivos de audio
- Notificaciones funcionando
- Sonidos de grabación

✅ **Integración con ZenMindConnect**
- Autenticación con Persona
- Conectado con sistema de reservas
- Notificaciones integradas
- Diseño consistente

---

## ⚠️ CONSIDERACIONES IMPORTANTES

### **NO SE PERDERÁ NADA**

1. ✅ **Audios**: Están en archivos estáticos, se copian tal cual
2. ✅ **Grabación**: MediaRecorder sigue funcionando igual
3. ✅ **Videollamada**: Agora SDK se mantiene intacto
4. ✅ **Funcionalidades**: Todo se preserva, solo se agrega chat

### **MEJORAS OPCIONALES FUTURAS**

1. ⏳ WebSockets en lugar de polling (mejor performance)
2. ⏳ Chat con archivos adjuntos
3. ⏳ Emojis y reacciones
4. ⏳ Búsqueda en historial
5. ⏳ Exportar conversación

---

## 📊 ESTIMACIÓN DE TIEMPO

| Fase | Tiempo | Prioridad |
|------|--------|-----------|
| Fase 1: Seguridad | 2-3h | 🔴 CRÍTICA |
| Fase 2: Modelos | 3-4h | 🔴 CRÍTICA |
| Fase 3: Vistas | 4-5h | 🔴 CRÍTICA |
| Fase 4: Frontend | 5-6h | 🔴 CRÍTICA |
| Fase 5: Reservas | 2-3h | 🟡 IMPORTANTE |
| Fase 6: Mejoras | 3-4h | 🟢 OPCIONAL |

**Total Mínimo**: 16-21 horas  
**Total Recomendado**: 19-25 horas (con mejoras)

---

## ✅ CONCLUSIÓN

**ES TOTALMENTE POSIBLE** integrar ambos proyectos sin perder funcionalidad.

**Ventajas**:
- ✅ Chat + Videollamada en una sola interfaz
- ✅ No se pierde nada (audios, grabaciones, funcionalidades)
- ✅ Mejor experiencia de usuario
- ✅ Integrado con ZenMindConnect

**Recomendación**: Proceder con la integración siguiendo este plan por fases.

---

*Última actualización: 2025-01-10*

