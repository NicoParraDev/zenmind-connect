/**
 * Sistema de chat integrado para videollamadas
 * Compatible con ZenMindConnect
 */

let CHAT_ROOM = sessionStorage.getItem('room');
let CHAT_USER = sessionStorage.getItem('name');

// Variable para rastrear los IDs de mensajes ya mostrados (evita parpadeo)
let loadedMessageIds = new Set();

// Variables para el indicador de escritura
let typingTimeout = null;
let isTyping = false;
let typingCheckInterval = null;

// Función para inicializar datos de chat
function initializeChatData() {
    if (!CHAT_ROOM) {
        // Intentar leer de la URL como fallback
        const urlParts = window.location.pathname.split('/');
        const roomFromUrl = urlParts[urlParts.length - 1];
        if (roomFromUrl && roomFromUrl !== 'room') {
            CHAT_ROOM = roomFromUrl;
            sessionStorage.setItem('room', CHAT_ROOM);
        }
    }
    
    if (!CHAT_USER) {
        // Intentar obtener del contexto de la página si está disponible
        const nameElement = document.querySelector('[data-user-name]');
        if (nameElement) {
            CHAT_USER = nameElement.getAttribute('data-user-name');
            sessionStorage.setItem('name', CHAT_USER);
        }
    }
    
    return CHAT_ROOM !== null;
}

// Función para obtener cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Función robusta para obtener CSRF token
function getCSRFToken() {
    const token = getCookie('csrftoken');
    if (!token || token.length < 10) {
        console.warn('Token CSRF no encontrado o inválido. Intentando obtener de meta tag...');
        // Intentar obtener del meta tag si existe
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            const metaToken = metaTag.getAttribute('content');
            if (metaToken && metaToken.length >= 10) {
                return metaToken;
            }
        }
        // Si aún no hay token, intentar obtener del input hidden si existe
        const csrfInput = document.querySelector('[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            const inputToken = csrfInput.value;
            if (inputToken && inputToken.length >= 10) {
                return inputToken;
            }
        }
        console.error('No se pudo obtener el token CSRF válido');
        return null;
    }
    return token;
}

// Cargar mensajes iniciales
function loadChatMessages() {
    // Inicializar datos si no están disponibles
    if (!CHAT_ROOM) {
        if (!initializeChatData()) {
            // Intentar leer de sessionStorage directamente
            CHAT_ROOM = sessionStorage.getItem('room');
            if (!CHAT_ROOM) {
                // Intentar leer de la URL como último recurso
                const urlParts = window.location.pathname.split('/');
                const roomFromUrl = urlParts[urlParts.length - 1];
                if (roomFromUrl && roomFromUrl !== 'room' && !roomFromUrl.includes('?')) {
                    CHAT_ROOM = roomFromUrl;
                    sessionStorage.setItem('room', CHAT_ROOM);
                }
            }
        }
    }
    
    if (!CHAT_ROOM) {
        console.warn('No hay sala definida, reintentando en 1 segundo...');
        // Reintentar después de un momento
        setTimeout(() => {
            loadChatMessages();
        }, 1000);
        return;
    }

    fetch(`/videocall/get_messages/${CHAT_ROOM}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al cargar mensajes');
            }
            return response.json();
        })
        .then(data => {
            const messagesContainer = document.getElementById('chat-messages');
            if (!messagesContainer) {
                console.error('Contenedor de mensajes no encontrado');
                return;
            }
            
            // Guardar el scroll position antes de actualizar
            const wasAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop <= messagesContainer.clientHeight + 100;
            
            if (!data.messages || data.messages.length === 0) {
                // Solo mostrar mensaje vacío si no hay mensajes y el contenedor está vacío
                if (messagesContainer.children.length === 0) {
                    messagesContainer.innerHTML = '<div class="no-messages">No hay mensajes aún. ¡Sé el primero en escribir!</div>';
                }
                return;
            }
            
            const currentUserName = (CHAT_USER || sessionStorage.getItem('name') || '').trim();
            let hasNewMessages = false;
            
            // Si es la primera carga, limpiar el contenedor y el set
            if (loadedMessageIds.size === 0) {
                messagesContainer.innerHTML = '';
                loadedMessageIds.clear();
            }
            
            // Agregar solo mensajes nuevos (evita parpadeo)
            data.messages.forEach((msg) => {
                if (!loadedMessageIds.has(msg.id)) {
                    hasNewMessages = true;
                    loadedMessageIds.add(msg.id);
                    
                    const messageDiv = document.createElement('div');
                    messageDiv.setAttribute('data-message-id', msg.id);
                    
                    // Determinar si es mensaje propio
                    const authorName = (msg.author || '').trim();
                    const isOwnMessage = currentUserName && (
                        authorName === currentUserName || 
                        authorName.toLowerCase() === currentUserName.toLowerCase()
                    );
                    
                    // Asignar clases correctamente
                    if (isOwnMessage) {
                        messageDiv.className = 'chat-message own-message';
                    } else {
                        messageDiv.className = 'chat-message other-message';
                    }
                    
                    messageDiv.innerHTML = `
                        <div class="message-header">
                            <strong>${escapeHtml(authorName || 'Usuario desconocido')}</strong>
                            <small>${new Date(msg.created_at).toLocaleTimeString('es-CL', {hour: '2-digit', minute: '2-digit'})}</small>
                        </div>
                        <div class="message-body">${escapeHtml(msg.message || '')}</div>
                    `;
                    // Agregar con transición suave
                    messageDiv.style.opacity = '0';
                    messageDiv.style.transform = 'translateY(10px)';
                    messagesContainer.appendChild(messageDiv);
                    
                    // Animar entrada
                    requestAnimationFrame(() => {
                        messageDiv.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
                        messageDiv.style.opacity = '1';
                        messageDiv.style.transform = 'translateY(0)';
                    });
                }
            });
            
            // Scroll al final solo si estaba al final antes o si hay mensajes nuevos
            if ((wasAtBottom || hasNewMessages) && messagesContainer.children.length > 0) {
                setTimeout(() => {
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }, 50);
            }
        })
        .catch(error => {
            console.error('Error cargando mensajes:', error);
        });
}

// Escapar HTML para seguridad
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Enviar mensaje
function sendChatMessage() {
    const input = document.getElementById('chat-input-field');
    if (!input) return;
    
    const message = input.value.trim();
    
    if (!message) return;
    
    if (!CHAT_ROOM) {
        alert('Error: No hay sala definida');
        return;
    }
    
    // Obtener token CSRF de forma robusta
    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        alert('Error: No se pudo obtener el token de seguridad. Por favor, recarga la página.');
        return;
    }
    
    fetch('/videocall/send_message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            room_name: CHAT_ROOM,
            message: message
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Error al enviar mensaje');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            input.value = '';
            // Detener indicador de escritura
            setTypingStatus(false);
            // Recargar mensajes después de un breve delay para que el servidor procese
            setTimeout(() => {
                loadChatMessages();
            }, 200);
        } else {
            alert('Error: ' + (data.error || 'No se pudo enviar el mensaje'));
        }
    })
    .catch(error => {
        console.error('Error enviando mensaje:', error);
        alert('Error: ' + error.message);
    });
}

// Función para establecer el estado de escritura
function setTypingStatus(typing) {
    if (!CHAT_ROOM) {
        console.warn('setTypingStatus: No hay CHAT_ROOM definido');
        return;
    }
    
    if (typing && !isTyping) {
        isTyping = true;
        console.log('Usuario empezó a escribir');
        notifyTypingStatus(true);
    } else if (!typing && isTyping) {
        isTyping = false;
        console.log('Usuario dejó de escribir');
        notifyTypingStatus(false);
    }
}

// Notificar al servidor el estado de escritura
function notifyTypingStatus(typing) {
    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        console.warn('notifyTypingStatus: No se pudo obtener CSRF token');
        return;
    }
    
    fetch('/videocall/set_typing/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            room_name: CHAT_ROOM,
            is_typing: typing
        })
    })
    .then(response => {
        if (!response.ok) {
            console.warn('notifyTypingStatus: Respuesta no OK', response.status);
        }
        return response.json();
    })
    .then(data => {
        if (data && data.success) {
            console.log('Estado de escritura notificado:', typing);
        }
    })
    .catch(error => {
        console.error('Error notificando estado de escritura:', error);
    });
}

// Función para obtener y mostrar quién está escribiendo
function checkTypingStatus() {
    if (!CHAT_ROOM) {
        console.warn('checkTypingStatus: No hay CHAT_ROOM definido');
        return;
    }
    
    fetch(`/videocall/get_typing/${CHAT_ROOM}/`)
        .then(response => {
            if (!response.ok) {
                console.warn('checkTypingStatus: Respuesta no OK', response.status);
                return null;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.typing_users && data.typing_users.length > 0) {
                console.log('Usuarios escribiendo:', data.typing_users);
                showTypingIndicator(data.typing_users);
            } else {
                hideTypingIndicator();
            }
        })
        .catch(error => {
            console.error('Error en checkTypingStatus:', error);
        });
}

// Mostrar indicador de escritura
function showTypingIndicator(users) {
    if (!users || users.length === 0) {
        hideTypingIndicator();
        return;
    }
    
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) {
        console.error('showTypingIndicator: Contenedor de mensajes no encontrado');
        return;
    }
    
    // Remover indicador anterior si existe
    const existingIndicator = document.getElementById('typing-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    // Crear nuevo indicador
    const typingContainer = document.createElement('div');
    typingContainer.id = 'typing-indicator';
    typingContainer.className = 'typing-indicator';
    
    let text = '';
    if (users.length === 1) {
        text = `${users[0]} está escribiendo...`;
    } else if (users.length === 2) {
        text = `${users[0]} y ${users[1]} están escribiendo...`;
    } else {
        text = `${users[0]} y ${users.length - 1} más están escribiendo...`;
    }
    
    typingContainer.innerHTML = `
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <span class="typing-text">${escapeHtml(text)}</span>
    `;
    
    // Agregar al final del contenedor de mensajes (debajo del último mensaje)
    messagesContainer.appendChild(typingContainer);
    
    // Asegurar que el indicador sea visible
    typingContainer.style.display = 'flex';
    typingContainer.style.opacity = '0';
    
    // Animar entrada suave
    requestAnimationFrame(() => {
        typingContainer.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
        typingContainer.style.opacity = '1';
        typingContainer.style.transform = 'translateY(0)';
    });
    
    // Scroll al final para ver el indicador (solo si estaba cerca del final)
    const wasAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop <= messagesContainer.clientHeight + 50;
    if (wasAtBottom) {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }
}

// Ocultar indicador de escritura
function hideTypingIndicator() {
    const typingContainer = document.getElementById('typing-indicator');
    if (typingContainer) {
        typingContainer.style.transition = 'opacity 0.3s ease-out';
        typingContainer.style.opacity = '0';
        setTimeout(() => {
            if (typingContainer && typingContainer.parentNode) {
                typingContainer.parentNode.removeChild(typingContainer);
            }
        }, 300);
    }
}

// Función para inicializar el chat cuando el DOM esté listo
function initializeChat() {
    // Inicializar datos de chat PRIMERO
    initializeChatData();
    
    // Actualizar CHAT_USER desde sessionStorage o data attribute
    if (!CHAT_USER) {
        const nameElement = document.querySelector('[data-user-name]');
        if (nameElement) {
            CHAT_USER = nameElement.getAttribute('data-user-name');
            sessionStorage.setItem('name', CHAT_USER);
            console.log('CHAT_USER inicializado desde data-user-name:', CHAT_USER);
        } else {
            CHAT_USER = sessionStorage.getItem('name');
            console.log('CHAT_USER obtenido de sessionStorage:', CHAT_USER);
        }
    }
    
    // Actualizar CHAT_ROOM
    if (!CHAT_ROOM) {
        CHAT_ROOM = sessionStorage.getItem('room');
        if (!CHAT_ROOM) {
            const urlParts = window.location.pathname.split('/');
            const roomFromUrl = urlParts[urlParts.length - 1];
            if (roomFromUrl && roomFromUrl !== 'room' && !roomFromUrl.includes('?')) {
                CHAT_ROOM = roomFromUrl;
                sessionStorage.setItem('room', CHAT_ROOM);
            }
        }
        console.log('CHAT_ROOM inicializado:', CHAT_ROOM);
    }
    
    const input = document.getElementById('chat-input-field');
    if (input) {
        // Remover listeners anteriores si existen
        const newInput = input.cloneNode(true);
        input.parentNode.replaceChild(newInput, input);
        
        // Detectar cuando el usuario está escribiendo
        let lastTypingTime = 0;
        newInput.addEventListener('input', function() {
            const now = Date.now();
            lastTypingTime = now;
            
            if (newInput.value.trim().length > 0) {
                // Notificar inmediatamente que está escribiendo
                if (!isTyping) {
                    setTypingStatus(true);
                }
                
                // Renovar el estado cada vez que escribe
                notifyTypingStatus(true);
                
                // Limpiar timeout anterior
                if (typingTimeout) {
                    clearTimeout(typingTimeout);
                }
                
                // Detener indicador después de 3 segundos sin escribir
                typingTimeout = setTimeout(() => {
                    const timeSinceLastTyping = Date.now() - lastTypingTime;
                    if (timeSinceLastTyping >= 3000) {
                        setTypingStatus(false);
                    }
                }, 3000);
            } else {
                setTypingStatus(false);
                if (typingTimeout) {
                    clearTimeout(typingTimeout);
                }
            }
        });
        
        newInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                setTypingStatus(false);
                if (typingTimeout) {
                    clearTimeout(typingTimeout);
                }
                sendChatMessage();
            }
        });
        
        // Detener indicador cuando se pierde el foco
        newInput.addEventListener('blur', function() {
            setTypingStatus(false);
            if (typingTimeout) {
                clearTimeout(typingTimeout);
            }
        });
        
        console.log('Input de chat conectado');
    } else {
        console.warn('Input de chat no encontrado, reintentando...');
        setTimeout(initializeChat, 500);
        return;
    }
    
    const sendButton = document.getElementById('chat-send-btn');
    if (sendButton) {
        // Remover listeners anteriores si existen
        const newSendButton = sendButton.cloneNode(true);
        sendButton.parentNode.replaceChild(newSendButton, sendButton);
        
        newSendButton.addEventListener('click', function(e) {
            e.preventDefault();
            sendChatMessage();
        });
        console.log('Botón de enviar chat conectado');
    } else {
        console.warn('Botón de enviar chat no encontrado, reintentando...');
        setTimeout(initializeChat, 500);
        return;
    }
    
        // Cargar mensajes iniciales
        console.log('Inicializando chat - CHAT_ROOM:', CHAT_ROOM, 'CHAT_USER:', CHAT_USER);
        loadChatMessages();
        
        // Polling para nuevos mensajes (cada 2 segundos)
        setInterval(() => {
            loadChatMessages();
        }, 2000);
        
        // Polling para indicador de escritura (cada 1 segundo)
        typingCheckInterval = setInterval(() => {
            checkTypingStatus();
        }, 1000);
}

// NO inicializar automáticamente - se inicializará cuando se muestre el panel de chat
// La inicialización se maneja desde videocall_room.html cuando se cambia al panel de chat

// Toggle chat panel
function toggleChat() {
    const chatPanel = document.getElementById('chat-panel');
    if (chatPanel) {
        chatPanel.classList.toggle('hidden');
    }
}

// Exportar funciones para uso global
window.videocallChat = {
    initializeChat: initializeChat,
    loadMessages: loadChatMessages,
    sendMessage: sendChatMessage,
    toggleChat: toggleChat
};

// Exponer initializeChat globalmente también
window.initializeChat = initializeChat;

