/**
 * Pizarra colaborativa para ZenMindConnect
 * Permite dibujar en tiempo real y sincronizar entre participantes
 */

let whiteboardCanvas = null;
let whiteboardCtx = null;
let isDrawing = false;
let currentTool = 'pen'; // 'pen', 'eraser', 'line', 'rectangle', 'circle', 'text', 'move', 'postit'
let currentColor = '#000000';
let currentLineWidth = 3;
let currentFontSize = 16; // Tamaño de fuente para texto
let currentFontFamily = 'Arial'; // Tipo de fuente para texto
let currentPostItColor = '#FFEB3B'; // Color de fondo para post-its (amarillo por defecto)
let lastX = 0;
let lastY = 0;
let startX = 0;
let startY = 0;
let isDrawingShape = false;
let tempCanvas = null; // Canvas temporal para previsualizar formas
let isWhiteboardOpen = false;
let drawingHistory = [];
let historyIndex = -1;
let lastSentActionId = null; // Para evitar procesar nuestros propios mensajes
let sentActionIds = new Set(); // Set para rastrear TODAS las acciones que hemos enviado
let actionCounter = 0; // Contador para IDs únicos de acciones
let selectedTextAction = null; // Texto seleccionado para mover
let isMovingText = false; // Flag para indicar que estamos moviendo texto
let textOffsetX = 0; // Offset X del clic dentro del texto
let textOffsetY = 0; // Offset Y del clic dentro del texto
let selectedPostItAction = null; // Post-it seleccionado para mover
let isMovingPostIt = false; // Flag para indicar que estamos moviendo post-it
let isResizingPostIt = false; // Flag para indicar que estamos redimensionando post-it
let postItOffsetX = 0; // Offset X del clic dentro del post-it
let postItOffsetY = 0; // Offset Y del clic dentro del post-it
let resizeHandle = null; // 'nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w' para las esquinas y bordes
let postItStartX = 0; // Posición X inicial del post-it al comenzar el resize
let postItStartY = 0; // Posición Y inicial del post-it al comenzar el resize
let postItStartWidth = 0; // Ancho inicial del post-it al comenzar el resize
let postItStartHeight = 0; // Alto inicial del post-it al comenzar el resize
let postItDeleteButton = null; // Botón de eliminar para post-its seleccionados

// Sistema de pizarras individuales
let currentWhiteboardMode = 'general'; // 'general' o 'user_UID'
let userWhiteboards = {}; // { 'general': { history: [], canvas: null }, 'user_33': { history: [], canvas: null } }
let currentUser = null;
let isCurrentlyDrawing = false; // Para el indicador
let drawingUsers = new Map(); // Mapa de usuarios que están dibujando { userName: timestamp }

// WebSocket para tiempo real (reemplaza polling)
let whiteboardSocket = null;
let websocketConnected = false;
let websocketReconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Inicializar pizarra
function initializeWhiteboard() {
    whiteboardCanvas = document.getElementById('whiteboard-canvas');
    if (!whiteboardCanvas) {
        console.error('[Whiteboard] ❌ Canvas de pizarra no encontrado en el DOM');
        return false;
    }
    
    whiteboardCtx = whiteboardCanvas.getContext('2d');
    if (!whiteboardCtx) {
        console.error('[Whiteboard] ❌ No se pudo obtener el contexto 2D del canvas');
        return false;
    }
    
    // Ajustar tamaño del canvas
    resizeCanvas();
    
    // Agregar listener de resize solo una vez
    if (!window.whiteboardResizeListenerAdded) {
    window.addEventListener('resize', resizeCanvas);
        window.whiteboardResizeListenerAdded = true;
    }
    
    // Eventos del mouse
    whiteboardCanvas.addEventListener('mousedown', startDrawing);
    whiteboardCanvas.addEventListener('mousemove', draw);
    whiteboardCanvas.addEventListener('mouseup', stopDrawing);
    whiteboardCanvas.addEventListener('mouseout', stopDrawing);
    
    // Evento para detectar cuando el mouse está sobre las esquinas de un post-it
    whiteboardCanvas.addEventListener('mousemove', (e) => {
        if (currentTool === 'move' && !isDrawing) {
            const rect = whiteboardCanvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const postItAction = getPostItAtPosition(x, y);
            if (postItAction && postItAction.resizeHandle) {
                // Cambiar cursor según el handle
                const cursorMap = {
                    'nw': 'nw-resize', 'ne': 'ne-resize', 'sw': 'sw-resize', 'se': 'se-resize',
                    'n': 'n-resize', 's': 's-resize', 'e': 'e-resize', 'w': 'w-resize'
                };
                whiteboardCanvas.style.cursor = cursorMap[postItAction.resizeHandle] || 'move';
            } else if (postItAction) {
                whiteboardCanvas.style.cursor = 'move';
            } else {
                // Verificar si hay un texto
                const textAction = getTextAtPosition(x, y);
                if (textAction) {
                    whiteboardCanvas.style.cursor = 'move';
                } else {
                    whiteboardCanvas.style.cursor = 'move';
                }
            }
        }
    });
    
    // Eventos táctiles (móvil)
    whiteboardCanvas.addEventListener('touchstart', handleTouchStart);
    whiteboardCanvas.addEventListener('touchmove', handleTouchMove);
    whiteboardCanvas.addEventListener('touchend', handleTouchEnd);
    
    // Evento de doble clic para editar texto
    whiteboardCanvas.addEventListener('dblclick', handleDoubleClick);
    
    // Evento de teclado para borrar post-its seleccionados (Delete o Backspace)
    if (!window.whiteboardKeyListenerAdded) {
        document.addEventListener('keydown', handleWhiteboardKeyDown);
        window.whiteboardKeyListenerAdded = true;
    }
    
    // Cargar dibujo guardado si existe
    loadSavedDrawing();
    
    // Redibujar desde el historial de la pizarra actual si hay acciones guardadas
    // Hacerlo inmediatamente para que las acciones se vean en tiempo real
    if (userWhiteboards[currentWhiteboardMode] && userWhiteboards[currentWhiteboardMode].history.length > 0) {
        redrawFromHistory();
    }
    
    // Configurar cursor inicial según la herramienta actual
    if (currentTool === 'pen') {
        whiteboardCanvas.style.cursor = 'crosshair';
    } else if (currentTool === 'eraser') {
        whiteboardCanvas.style.cursor = 'grab';
    } else if (currentTool === 'line' || currentTool === 'rectangle' || currentTool === 'circle') {
        whiteboardCanvas.style.cursor = 'crosshair';
    } else if (currentTool === 'text') {
        whiteboardCanvas.style.cursor = 'text';
    } else if (currentTool === 'move') {
        whiteboardCanvas.style.cursor = 'move';
    } else if (currentTool === 'postit') {
        whiteboardCanvas.style.cursor = 'crosshair';
    } else {
        whiteboardCanvas.style.cursor = 'default';
    }
    
    console.log('[Whiteboard] ✅ Pizarra inicializada correctamente');
    return true;
}

// Redimensionar canvas
function resizeCanvas() {
    if (!whiteboardCanvas) return;
    
    const container = whiteboardCanvas.parentElement;
    if (!container) return;
    
    const rect = container.getBoundingClientRect();
    whiteboardCanvas.width = rect.width;
    whiteboardCanvas.height = rect.height;
    
    // Redibujar desde el historial
    redrawFromHistory();
}

// Verificar si el usuario puede editar la pizarra actual
function canEditCurrentWhiteboard() {
    const currentUID = getCurrentUID();
    
    // Si no hay UID, no permitir edición (por seguridad)
    if (!currentUID) {
        console.warn('[Whiteboard] ⚠️ No se pudo obtener UID del usuario');
        return false;
    }
    
    // Pizarra general: todos pueden editar
    if (currentWhiteboardMode === 'general') {
        return true;
    }
    
    // Pizarra de usuario: solo el dueño puede editar
    if (currentWhiteboardMode.startsWith('user_')) {
        const ownerUID = currentWhiteboardMode.replace('user_', '');
        // Comparar como strings para asegurar coincidencia
        const canEdit = String(ownerUID) === String(currentUID);
        console.log('[Whiteboard] 🔐 Verificación de permisos:', {
            currentUID: String(currentUID),
            ownerUID: String(ownerUID),
            currentMode: currentWhiteboardMode,
            canEdit: canEdit
        });
        return canEdit;
    }
    
    // Por defecto, no permitir edición
    return false;
}

// Detectar si un clic está sobre un texto
function getTextAtPosition(x, y) {
    if (!userWhiteboards[currentWhiteboardMode]) {
        return null;
    }
    
    const history = userWhiteboards[currentWhiteboardMode].history;
    
    // Buscar desde el final hacia el principio (textos más recientes primero)
    for (let i = history.length - 1; i >= 0; i--) {
        const action = history[i];
        if (action.type === 'text') {
            // Calcular el área del texto
            let textX = action.x;
            let textY = action.y;
            let textWidth = action.width || 200; // Ancho por defecto si no hay
            let textHeight = action.height || 30; // Alto por defecto si no hay
            
            // Si el texto tiene width y height, usar esos valores
            if (action.width && action.height) {
                textWidth = action.width;
                textHeight = action.height;
            } else {
                // Calcular dimensiones aproximadas del texto
                if (whiteboardCtx) {
                    whiteboardCtx.font = `${action.fontSize || 16}px ${action.fontFamily || 'Arial'}`;
                    const metrics = whiteboardCtx.measureText(action.text || '');
                    textWidth = metrics.width + 16; // +16 para padding
                    textHeight = (action.fontSize || 16) * 1.5;
                }
            }
            
            // Verificar si el clic está dentro del área del texto
            if (x >= textX && x <= textX + textWidth && 
                y >= textY && y <= textY + textHeight) {
                return action;
            }
        }
    }
    
    return null;
}

// Detectar si un clic está sobre un post-it y en qué parte (esquina, borde o centro)
function getPostItAtPosition(x, y) {
    if (!userWhiteboards[currentWhiteboardMode]) {
        return null;
    }
    
    const history = userWhiteboards[currentWhiteboardMode].history;
    const handleSize = 10; // Tamaño del área de redimensionamiento en las esquinas
    
    // Buscar desde el final hacia el principio (post-its más recientes primero)
    for (let i = history.length - 1; i >= 0; i--) {
        const action = history[i];
        if (action.type === 'postit') {
            // Calcular el área del post-it
            const postItX = action.x;
            const postItY = action.y;
            const postItWidth = action.width || 200;
            const postItHeight = action.height || 150;
            
            // Verificar si el clic está dentro del área del post-it
            if (x >= postItX && x <= postItX + postItWidth && 
                y >= postItY && y <= postItY + postItHeight) {
                // Detectar si el clic está en una esquina o borde para redimensionar
                const isNearLeft = Math.abs(x - postItX) < handleSize;
                const isNearRight = Math.abs(x - (postItX + postItWidth)) < handleSize;
                const isNearTop = Math.abs(y - postItY) < handleSize;
                const isNearBottom = Math.abs(y - (postItY + postItHeight)) < handleSize;
                
                // Determinar el handle de redimensionamiento
                if (isNearTop && isNearLeft) {
                    action.resizeHandle = 'nw';
                } else if (isNearTop && isNearRight) {
                    action.resizeHandle = 'ne';
                } else if (isNearBottom && isNearLeft) {
                    action.resizeHandle = 'sw';
                } else if (isNearBottom && isNearRight) {
                    action.resizeHandle = 'se';
                } else if (isNearTop) {
                    action.resizeHandle = 'n';
                } else if (isNearBottom) {
                    action.resizeHandle = 's';
                } else if (isNearLeft) {
                    action.resizeHandle = 'w';
                } else if (isNearRight) {
                    action.resizeHandle = 'e';
                } else {
                    action.resizeHandle = null; // Centro, para mover
                }
                
                return action;
            }
        }
    }
    
    return null;
}

// Mostrar botón de eliminar para post-it seleccionado
function showPostItDeleteButton(postItAction) {
    if (!postItAction || !whiteboardCanvas) return;
    
    // Obtener contenedor del canvas
    const canvasContainer = whiteboardCanvas.parentElement;
    if (!canvasContainer) return;
    
    // Si el botón ya existe, actualizar posición
    if (postItDeleteButton) {
        updatePostItDeleteButtonPosition(postItAction);
        postItDeleteButton.style.display = 'flex';
        return;
    }
    
    // Crear botón de eliminar
    postItDeleteButton = document.createElement('button');
    postItDeleteButton.innerHTML = '<i class="fas fa-trash"></i>';
    postItDeleteButton.className = 'postit-delete-btn';
    postItDeleteButton.title = 'Eliminar post-it (o presiona Delete/Suprimir)';
    postItDeleteButton.style.cssText = `
        position: absolute;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #ff4444;
        color: white;
        border: 2px solid white;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10001;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease;
        font-size: 14px;
    `;
    
    // Efecto hover
    postItDeleteButton.addEventListener('mouseenter', () => {
        postItDeleteButton.style.background = '#cc0000';
        postItDeleteButton.style.transform = 'scale(1.15)';
    });
    postItDeleteButton.addEventListener('mouseleave', () => {
        postItDeleteButton.style.background = '#ff4444';
        postItDeleteButton.style.transform = 'scale(1)';
    });
    
    // Click para borrar
    postItDeleteButton.addEventListener('click', (e) => {
        e.stopPropagation(); // Evitar que se propague al canvas
        if (selectedPostItAction && selectedPostItAction.id) {
            console.log('[Whiteboard] 🗑️ Borrando post-it desde botón de eliminar:', {
                postItId: selectedPostItAction.id
            });
            deletePostIt(selectedPostItAction);
            hidePostItDeleteButton();
        }
    });
    
    // Agregar al contenedor
    canvasContainer.appendChild(postItDeleteButton);
    
    // Posicionar el botón
    updatePostItDeleteButtonPosition(postItAction);
}

// Actualizar posición del botón de eliminar
function updatePostItDeleteButtonPosition(postItAction) {
    if (!postItDeleteButton || !postItAction || !whiteboardCanvas) return;
    
    const canvasContainer = whiteboardCanvas.parentElement;
    if (!canvasContainer) return;
    
    // Obtener posición del canvas relativa al contenedor
    const canvasRect = whiteboardCanvas.getBoundingClientRect();
    const containerRect = canvasContainer.getBoundingClientRect();
    
    // Calcular posición del botón (esquina superior derecha del post-it)
    const postItX = postItAction.x;
    const postItY = postItAction.y;
    const postItWidth = postItAction.width || 200;
    
    // Posición relativa al contenedor
    const buttonX = (canvasRect.left - containerRect.left) + postItX + postItWidth - 16; // 16px desde el borde derecho
    const buttonY = (canvasRect.top - containerRect.top) + postItY - 16; // 16px desde el borde superior
    
    postItDeleteButton.style.left = buttonX + 'px';
    postItDeleteButton.style.top = buttonY + 'px';
}

// Ocultar botón de eliminar
function hidePostItDeleteButton() {
    if (postItDeleteButton) {
        postItDeleteButton.style.display = 'none';
    }
}

// Manejar teclas para borrar post-its seleccionados
function handleWhiteboardKeyDown(e) {
    // Solo procesar si la pizarra está abierta y visible
    if (!isWhiteboardOpen || !whiteboardCanvas) return;
    
    // Detectar Delete/Suprimir o Backspace (compatibilidad con diferentes navegadores y teclados)
    const isDeleteKey = e.key === 'Delete' || 
                        e.key === 'Del' || 
                        e.code === 'Delete' || 
                        e.keyCode === 46;
    const isBackspaceKey = e.key === 'Backspace' || 
                           e.code === 'Backspace' || 
                           e.keyCode === 8;
    
    if (!isDeleteKey && !isBackspaceKey) return;
    
    // Evitar borrar si estamos escribiendo en un input o textarea
    const activeElement = document.activeElement;
    if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
        return;
    }
    
    // Si hay un post-it seleccionado, borrarlo
    if (selectedPostItAction && selectedPostItAction.id) {
        e.preventDefault(); // Evitar comportamiento por defecto del navegador
        console.log('[Whiteboard] 🗑️ Borrando post-it seleccionado con tecla Delete/Backspace:', {
            postItId: selectedPostItAction.id,
            key: e.key,
            code: e.code,
            keyCode: e.keyCode
        });
        deletePostIt(selectedPostItAction);
        // Limpiar selección después de borrar
        selectedPostItAction = null;
        isMovingPostIt = false;
        isResizingPostIt = false;
        hidePostItDeleteButton();
    }
}

// Iniciar dibujo
function startDrawing(e) {
    if (!whiteboardCtx) return;
    
    // Verificar permisos de edición
    if (!canEditCurrentWhiteboard()) {
        // Mostrar mensaje de solo lectura
        const canvas = whiteboardCanvas;
        if (canvas) {
            canvas.style.cursor = 'not-allowed';
            // Mostrar tooltip temporal
            const tooltip = document.createElement('div');
            tooltip.textContent = 'Solo lectura: Esta pizarra pertenece a otro usuario';
            tooltip.style.cssText = 'position: absolute; background: rgba(0,0,0,0.8); color: white; padding: 8px; border-radius: 4px; pointer-events: none; z-index: 10000;';
            tooltip.style.left = e.clientX + 'px';
            tooltip.style.top = (e.clientY - 30) + 'px';
            document.body.appendChild(tooltip);
            setTimeout(() => {
                document.body.removeChild(tooltip);
                canvas.style.cursor = 'default';
            }, 2000);
        }
        return;
    }
    
    const rect = whiteboardCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Si la herramienta es "eraser" y hacemos clic en un post-it, borrarlo
    if (currentTool === 'eraser') {
        const postItAction = getPostItAtPosition(x, y);
        if (postItAction) {
            // Borrar el post-it
            deletePostIt(postItAction);
            return;
        }
    }
    
    // Si la herramienta es "move" o si hacemos clic en un texto o post-it, intentar moverlo o redimensionarlo
    if (currentTool === 'move') {
        // Priorizar post-its sobre texto
        const postItAction = getPostItAtPosition(x, y);
        if (postItAction) {
            selectedPostItAction = postItAction;
            
            // Mostrar botón de eliminar
            showPostItDeleteButton(postItAction);
            
            // Si el clic está en una esquina o borde, redimensionar; si no, mover
            if (postItAction.resizeHandle) {
                isResizingPostIt = true;
                isMovingPostIt = false;
                resizeHandle = postItAction.resizeHandle;
                postItStartX = postItAction.x;
                postItStartY = postItAction.y;
                postItStartWidth = postItAction.width || 200;
                postItStartHeight = postItAction.height || 150;
                startX = x;
                startY = y;
                
                // Cambiar cursor según el handle
                const cursorMap = {
                    'nw': 'nw-resize', 'ne': 'ne-resize', 'sw': 'sw-resize', 'se': 'se-resize',
                    'n': 'n-resize', 's': 's-resize', 'e': 'e-resize', 'w': 'w-resize'
                };
                whiteboardCanvas.style.cursor = cursorMap[resizeHandle] || 'move';
            } else {
                isMovingPostIt = true;
                isResizingPostIt = false;
                resizeHandle = null;
                postItOffsetX = x - postItAction.x;
                postItOffsetY = y - postItAction.y;
                whiteboardCanvas.style.cursor = 'move';
            }
            
            isDrawing = true;
            lastX = x;
            lastY = y;
            return;
        }
        const textAction = getTextAtPosition(x, y);
        if (textAction) {
            selectedTextAction = textAction;
            isMovingText = true;
            isDrawing = true;
            startX = x;
            startY = y;
            textOffsetX = x - textAction.x;
            textOffsetY = y - textAction.y;
            lastX = x;
            lastY = y;
            whiteboardCanvas.style.cursor = 'move';
            return;
        } else {
            // No hay texto o post-it en esa posición, ocultar botón de eliminar si estaba visible
            hidePostItDeleteButton();
            selectedPostItAction = null;
            return;
        }
    }
    
    // Si no es "move", verificar si hacemos clic en un texto o post-it (para moverlo sin cambiar herramienta)
    // Solo si no estamos usando otra herramienta de dibujo
    if (currentTool !== 'pen' && currentTool !== 'eraser' && 
        currentTool !== 'line' && currentTool !== 'rectangle' && 
        currentTool !== 'circle' && currentTool !== 'text' && currentTool !== 'postit') {
        // Priorizar post-its sobre texto
        const postItAction = getPostItAtPosition(x, y);
        if (postItAction) {
            selectedPostItAction = postItAction;
            
            // Mostrar botón de eliminar
            showPostItDeleteButton(postItAction);
            
            // Si el clic está en una esquina o borde, redimensionar; si no, mover
            if (postItAction.resizeHandle) {
                isResizingPostIt = true;
                isMovingPostIt = false;
                resizeHandle = postItAction.resizeHandle;
                postItStartX = postItAction.x;
                postItStartY = postItAction.y;
                postItStartWidth = postItAction.width || 200;
                postItStartHeight = postItAction.height || 150;
                startX = x;
                startY = y;
                
                // Cambiar cursor según el handle
                const cursorMap = {
                    'nw': 'nw-resize', 'ne': 'ne-resize', 'sw': 'sw-resize', 'se': 'se-resize',
                    'n': 'n-resize', 's': 's-resize', 'e': 'e-resize', 'w': 'w-resize'
                };
                whiteboardCanvas.style.cursor = cursorMap[resizeHandle] || 'move';
            } else {
                isMovingPostIt = true;
                isResizingPostIt = false;
                resizeHandle = null;
                postItOffsetX = x - postItAction.x;
                postItOffsetY = y - postItAction.y;
                whiteboardCanvas.style.cursor = 'move';
            }
            
            isDrawing = true;
            lastX = x;
            lastY = y;
            return;
        }
        const textAction = getTextAtPosition(x, y);
        if (textAction) {
            selectedTextAction = textAction;
            isMovingText = true;
            isDrawing = true;
            startX = x;
            startY = y;
            textOffsetX = x - textAction.x;
            textOffsetY = y - textAction.y;
            lastX = x;
            lastY = y;
            whiteboardCanvas.style.cursor = 'move';
            return;
        }
    }
    
    // Para formas (línea, rectángulo, círculo, texto, postit), guardar punto inicial
    if (currentTool === 'line' || currentTool === 'rectangle' || currentTool === 'circle' || currentTool === 'text' || currentTool === 'postit') {
        isDrawing = true;
        isDrawingShape = true;
        startX = x;
        startY = y;
        lastX = x;
        lastY = y;
        return;
    }
    
    // Para lápiz y borrador (comportamiento normal)
    isDrawing = true;
    lastX = x;
    lastY = y;
    
    // LOG ESPECÍFICO PARA BORRADOR AL INICIAR DIBUJO
    if (currentTool === 'eraser') {
        console.log('[Whiteboard] 🧹 INICIANDO BORRADO (mousedown):', {
            x: x,
            y: y,
            currentTool: currentTool,
            isDrawing: isDrawing,
            timestamp: new Date().toISOString()
        });
    }
}

// Dibujar
function draw(e) {
    if (!isDrawing || !whiteboardCtx) return;
    
    // Verificar permisos de edición antes de dibujar
    if (!canEditCurrentWhiteboard()) {
        isDrawing = false;
        return;
    }
    
    const rect = whiteboardCanvas.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;
    
    // LOG ESPECÍFICO PARA BORRADOR EN CADA MOVIMIENTO (solo el primero para no saturar)
    if (currentTool === 'eraser' && !window._eraserLogShown) {
        console.log('[Whiteboard] 🧹 DIBUJANDO CON BORRADOR (mousemove):', {
            fromX: lastX,
            fromY: lastY,
            toX: currentX,
            toY: currentY,
            currentTool: currentTool,
            isDrawing: isDrawing,
            timestamp: new Date().toISOString()
        });
        window._eraserLogShown = true;
        // Resetear después de 1 segundo para permitir nuevos logs
        setTimeout(() => { window._eraserLogShown = false; }, 1000);
    }
    
    // Si estamos redimensionando post-it, actualizar tamaño y redibujar
    if (isResizingPostIt && selectedPostItAction && resizeHandle) {
        // Calcular el desplazamiento del mouse
        const deltaX = currentX - startX;
        const deltaY = currentY - startY;
        
        // Calcular nuevo tamaño y posición según el handle
        let newX = postItStartX;
        let newY = postItStartY;
        let newWidth = postItStartWidth;
        let newHeight = postItStartHeight;
        
        // Aplicar cambios según el handle de redimensionamiento
        if (resizeHandle.includes('e')) { // Este (derecha)
            newWidth = Math.max(50, postItStartWidth + deltaX);
        }
        if (resizeHandle.includes('w')) { // Oeste (izquierda)
            newWidth = Math.max(50, postItStartWidth - deltaX);
            newX = postItStartX + deltaX;
        }
        if (resizeHandle.includes('s')) { // Sur (abajo)
            newHeight = Math.max(50, postItStartHeight + deltaY);
        }
        if (resizeHandle.includes('n')) { // Norte (arriba)
            newHeight = Math.max(50, postItStartHeight - deltaY);
            newY = postItStartY + deltaY;
        }
        
        // Redibujar desde el historial (sin el post-it que estamos redimensionando)
        redrawFromHistoryExcluding(selectedPostItAction.id);
        
        // Actualizar posición del botón de eliminar durante el redimensionamiento
        const tempPostIt = {
            ...selectedPostItAction,
            x: newX,
            y: newY,
            width: newWidth,
            height: newHeight
        };
        updatePostItDeleteButtonPosition(tempPostIt);
        
        // Dibujar el post-it con el nuevo tamaño temporalmente
        drawPostIt(tempPostIt);
        
        // Enviar actualización en tiempo real a otros usuarios (throttled)
        const now = Date.now();
        if (!selectedPostItAction.lastResizeTime || (now - selectedPostItAction.lastResizeTime) > 16) {
            const actionId = `resize_${Date.now()}_${++actionCounter}`;
            const currentUID = getCurrentUID();
            const currentUserName = getCurrentUser();
            const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
            
            const resizeAction = {
                id: actionId,
                type: 'postit_resize',
                originalId: selectedPostItAction.id,
                x: newX,
                y: newY,
                width: newWidth,
                height: newHeight,
                userId: currentUID,
                userName: currentUserName,
                whiteboardMode: currentWhiteboardMode,
                created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico
                created_at_iso: new Date().toISOString()
            };
            
            // Actualizar tamaño temporal en el historial
            const history = userWhiteboards[currentWhiteboardMode].history;
            const actionIndex = history.findIndex(a => a.id === selectedPostItAction.id);
            if (actionIndex !== -1) {
                history[actionIndex].x = newX;
                history[actionIndex].y = newY;
                history[actionIndex].width = newWidth;
                history[actionIndex].height = newHeight;
            }
            
            lastSentActionId = actionId;
            sentActionIds.add(actionId);
            
            if (sentActionIds.size > 1000) {
                sentActionIds.clear();
                if (lastSentActionId) {
                    sentActionIds.add(lastSentActionId);
                }
            }
            
            sendDrawingAction(resizeAction);
            selectedPostItAction.lastResizeTime = now;
        }
        
        lastX = currentX;
        lastY = currentY;
        return;
    }
    
    // Si estamos moviendo post-it, actualizar posición y redibujar
    if (isMovingPostIt && selectedPostItAction) {
        // Calcular nueva posición del post-it
        const newX = currentX - postItOffsetX;
        const newY = currentY - postItOffsetY;
        
        // Actualizar posición temporal del post-it para el botón de eliminar
        const tempPostIt = { ...selectedPostItAction, x: newX, y: newY };
        updatePostItDeleteButtonPosition(tempPostIt);
        
        // Redibujar desde el historial (sin el post-it que estamos moviendo)
        redrawFromHistoryExcluding(selectedPostItAction.id);
        
        // Dibujar el post-it en la nueva posición temporalmente
        drawPostIt(selectedPostItAction, newX, newY);
        
        // Enviar actualización en tiempo real a otros usuarios (throttled)
        const now = Date.now();
        if (!selectedPostItAction.lastMoveTime || (now - selectedPostItAction.lastMoveTime) > 16) {
            const actionId = `move_${Date.now()}_${++actionCounter}`;
            const currentUID = getCurrentUID();
            const currentUserName = getCurrentUser();
            const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
            
            const moveAction = {
                id: actionId,
                type: 'postit_move',
                originalId: selectedPostItAction.id,
                x: newX,
                y: newY,
                userId: currentUID,
                userName: currentUserName,
                whiteboardMode: currentWhiteboardMode,
                created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico
                created_at_iso: new Date().toISOString()
            };
            
            // Actualizar posición temporal en el historial
            const history = userWhiteboards[currentWhiteboardMode].history;
            const actionIndex = history.findIndex(a => a.id === selectedPostItAction.id);
            if (actionIndex !== -1) {
                history[actionIndex].x = newX;
                history[actionIndex].y = newY;
            }
            
            lastSentActionId = actionId;
            sentActionIds.add(actionId);
            
            if (sentActionIds.size > 1000) {
                sentActionIds.clear();
                if (lastSentActionId) {
                    sentActionIds.add(lastSentActionId);
                }
            }
            
            sendDrawingAction(moveAction);
            selectedPostItAction.lastMoveTime = now;
        }
        
        lastX = currentX;
        lastY = currentY;
        return;
    }
    
    // Si estamos moviendo texto, actualizar posición y redibujar
    if (isMovingText && selectedTextAction) {
        // Calcular nueva posición del texto
        const newX = currentX - textOffsetX;
        const newY = currentY - textOffsetY;
        
        // Redibujar desde el historial (sin el texto que estamos moviendo)
        redrawFromHistoryExcluding(selectedTextAction.id);
        
        // Dibujar el texto en la nueva posición temporalmente (SOLO visual, no guardar)
        drawTextOnly(newX, newY, selectedTextAction.text, 
                    selectedTextAction.width, selectedTextAction.height,
                    selectedTextAction.color, selectedTextAction.fontSize, selectedTextAction.fontFamily);
        
        // Enviar actualización en tiempo real a otros usuarios (throttled para no saturar)
        // Reducir throttling a 16ms (~60fps) para movimiento más fluido, similar al dibujo
        const now = Date.now();
        if (!selectedTextAction.lastMoveTime || (now - selectedTextAction.lastMoveTime) > 16) {
            const actionId = `move_${Date.now()}_${++actionCounter}`;
            const currentUID = getCurrentUID();
            const currentUserName = getCurrentUser();
            const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
            
            const moveAction = {
                id: actionId,
                type: 'text_move',
                originalId: selectedTextAction.id,
                x: newX,
                y: newY,
                userId: currentUID,
                userName: currentUserName,
                whiteboardMode: currentWhiteboardMode,
                created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico
                created_at_iso: new Date().toISOString()
            };
            
            // NO actualizar el historial durante el movimiento - solo actualizar visualmente
            // El historial se actualizará solo cuando se suelte el mouse (en stopDrawing)
            // Esto evita que se creen múltiples copias del texto durante el movimiento
            
            // Guardar ID y enviar a otros usuarios inmediatamente
            lastSentActionId = actionId;
            sentActionIds.add(actionId);
            
            // Limpiar el Set si crece demasiado
            if (sentActionIds.size > 1000) {
                sentActionIds.clear();
                if (lastSentActionId) {
                    sentActionIds.add(lastSentActionId);
                }
            }
            
            // Enviar a otros usuarios inmediatamente
            sendDrawingAction(moveAction);
            selectedTextAction.lastMoveTime = now;
        }
        
        lastX = currentX;
        lastY = currentY;
        return;
    }
    
    // Si estamos dibujando una forma, previsualizar
    if (isDrawingShape && (currentTool === 'line' || currentTool === 'rectangle' || currentTool === 'circle' || currentTool === 'text' || currentTool === 'postit')) {
        // Redibujar desde el historial para limpiar la previsualización anterior
        redrawFromHistory();
        // Previsualizar la forma
        if (currentTool === 'text') {
            previewTextRect(startX, startY, currentX, currentY);
        } else if (currentTool === 'postit') {
            previewPostIt(startX, startY, currentX, currentY);
        } else {
            previewShape(startX, startY, currentX, currentY);
        }
        return;
    }
    
    // Para lápiz y borrador (comportamiento normal)
    // NO dibujar si la herramienta es texto, postit, línea, rectángulo o círculo (solo previsualizar)
    if (currentTool === 'text' || currentTool === 'postit' || 
        currentTool === 'line' || currentTool === 'rectangle' || currentTool === 'circle') {
        // Estas herramientas solo deben previsualizar, no dibujar trazos
        return;
    }
    
    whiteboardCtx.beginPath();
    whiteboardCtx.moveTo(lastX, lastY);
    whiteboardCtx.lineTo(currentX, currentY);
    
    if (currentTool === 'pen') {
        whiteboardCtx.strokeStyle = currentColor;
        whiteboardCtx.lineWidth = currentLineWidth;
        whiteboardCtx.lineCap = 'round';
        whiteboardCtx.lineJoin = 'round';
    } else if (currentTool === 'eraser') {
        whiteboardCtx.strokeStyle = '#ffffff';
        whiteboardCtx.lineWidth = currentLineWidth * 2;
        whiteboardCtx.globalCompositeOperation = 'destination-out';
    }
    
    whiteboardCtx.stroke();
    
    // Crear acción con ID único
    const actionId = `action_${Date.now()}_${++actionCounter}`;
    const currentUID = getCurrentUID();
    const currentUserName = getCurrentUser();
    const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
    
    const action = {
        id: actionId,
        type: 'draw',
        fromX: lastX,
        fromY: lastY,
        toX: currentX,
        toY: currentY,
        tool: currentTool,
        color: currentColor,
        lineWidth: currentLineWidth,
        userId: currentUID,
        userName: currentUserName,
        whiteboardMode: currentWhiteboardMode, // Indica en qué pizarra se dibuja
        created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico para ordenamiento correcto
        created_at_iso: new Date().toISOString() // Formato ISO para logs
    };
    
    // LOG ESPECÍFICO PARA BORRADO LOCAL
    if (currentTool === 'eraser') {
        console.log('[Whiteboard] ✏️ DIBUJANDO BORRADO LOCAL:', {
            actionId: actionId,
            fromX: lastX,
            fromY: lastY,
            toX: currentX,
            toY: currentY,
            lineWidth: currentLineWidth,
            whiteboardMode: currentWhiteboardMode
        });
    }
    
    // Guardar en historial de la pizarra actual
    saveToHistory(action);
    
    // Guardar ID de la última acción enviada y agregar al Set de acciones enviadas
    lastSentActionId = actionId;
    sentActionIds.add(actionId);
    
    // Limpiar el Set si crece demasiado (más de 1000 acciones)
    if (sentActionIds.size > 1000) {
        sentActionIds.clear();
        // Mantener al menos la última acción
        if (lastSentActionId) {
            sentActionIds.add(lastSentActionId);
        }
    }
    
    // Mostrar indicador de que estamos dibujando
    isCurrentlyDrawing = true;
    showDrawingIndicator(currentUserName);
    
    // Enviar a otros participantes (logs eliminados para mejorar rendimiento)
    sendDrawingAction(action);
    
    lastX = currentX;
    lastY = currentY;
    
    if (currentTool === 'eraser') {
        whiteboardCtx.globalCompositeOperation = 'source-over';
    }
}

// Redibujar desde historial excluyendo una acción específica
function redrawFromHistoryExcluding(excludeActionId) {
    if (!whiteboardCtx || !whiteboardCanvas) return;
    
    // Limpiar canvas
    whiteboardCtx.clearRect(0, 0, whiteboardCanvas.width, whiteboardCanvas.height);
    
    // Obtener historial de la pizarra actual
    if (!userWhiteboards[currentWhiteboardMode]) {
        initializeUserWhiteboard(currentWhiteboardMode);
    }
    
    const currentBoard = userWhiteboards[currentWhiteboardMode];
    const historyToDraw = currentBoard.history.filter(action => action.id !== excludeActionId);
    
    // Redibujar todas las acciones excepto la excluida
    historyToDraw.forEach(action => {
        if (action.type === 'draw') {
            whiteboardCtx.beginPath();
            whiteboardCtx.moveTo(action.fromX, action.fromY);
            whiteboardCtx.lineTo(action.toX, action.toY);
            
            if (action.tool === 'pen') {
                whiteboardCtx.strokeStyle = action.color;
                whiteboardCtx.globalCompositeOperation = 'source-over';
            } else if (action.tool === 'eraser') {
                whiteboardCtx.strokeStyle = '#ffffff';
                whiteboardCtx.globalCompositeOperation = 'destination-out';
            }
            
            whiteboardCtx.lineWidth = action.lineWidth;
            whiteboardCtx.lineCap = 'round';
            whiteboardCtx.lineJoin = 'round';
            whiteboardCtx.stroke();
            
            if (action.tool === 'eraser') {
                whiteboardCtx.globalCompositeOperation = 'source-over';
            }
        } else if (action.type === 'shape') {
            whiteboardCtx.strokeStyle = action.color;
            whiteboardCtx.lineWidth = action.lineWidth;
            whiteboardCtx.globalCompositeOperation = 'source-over';
            
            if (action.tool === 'line') {
                whiteboardCtx.beginPath();
                whiteboardCtx.moveTo(action.fromX, action.fromY);
                whiteboardCtx.lineTo(action.toX, action.toY);
                whiteboardCtx.stroke();
            } else if (action.tool === 'rectangle') {
                whiteboardCtx.strokeRect(action.x, action.y, action.width, action.height);
            } else if (action.tool === 'circle') {
                whiteboardCtx.beginPath();
                whiteboardCtx.arc(action.centerX, action.centerY, action.radius, 0, 2 * Math.PI);
                whiteboardCtx.stroke();
            }
        } else if (action.type === 'text') {
            whiteboardCtx.fillStyle = action.color;
            const fontSize = action.fontSize || 16;
            const fontFamily = action.fontFamily || 'Arial';
            whiteboardCtx.font = `${fontSize}px ${fontFamily}`;
            
            if (action.width && action.height) {
                const lines = wrapText(action.text, action.width - 16, fontSize, fontFamily);
                const lineHeight = fontSize * 1.2;
                const startY = action.y + fontSize + 4;
                
                lines.forEach((line, index) => {
                    const lineY = startY + (index * lineHeight);
                    if (lineY <= action.y + action.height - 4) {
                        whiteboardCtx.fillText(line, action.x + 8, lineY);
                    }
                });
            } else {
                whiteboardCtx.fillText(action.text, action.x, action.y);
            }
        } else if (action.type === 'postit') {
            drawPostIt(action);
        } else if (action.type === 'clear') {
            whiteboardCtx.clearRect(0, 0, whiteboardCanvas.width, whiteboardCanvas.height);
        }
    });
}

// Detener dibujo
function stopDrawing(e) {
    if (!isDrawing) return;
    
    // Si estábamos redimensionando post-it, actualizar su tamaño en el historial
    if (isResizingPostIt && selectedPostItAction && resizeHandle) {
        const rect = whiteboardCanvas.getBoundingClientRect();
        const endX = e ? (e.clientX - rect.left) : lastX;
        const endY = e ? (e.clientY - rect.top) : lastY;
        
        // Calcular el desplazamiento del mouse
        const deltaX = endX - startX;
        const deltaY = endY - startY;
        
        // Calcular nuevo tamaño y posición según el handle
        let newX = postItStartX;
        let newY = postItStartY;
        let newWidth = postItStartWidth;
        let newHeight = postItStartHeight;
        
        // Aplicar cambios según el handle de redimensionamiento
        if (resizeHandle.includes('e')) { // Este (derecha)
            newWidth = Math.max(50, postItStartWidth + deltaX);
        }
        if (resizeHandle.includes('w')) { // Oeste (izquierda)
            newWidth = Math.max(50, postItStartWidth - deltaX);
            newX = postItStartX + deltaX;
        }
        if (resizeHandle.includes('s')) { // Sur (abajo)
            newHeight = Math.max(50, postItStartHeight + deltaY);
        }
        if (resizeHandle.includes('n')) { // Norte (arriba)
            newHeight = Math.max(50, postItStartHeight - deltaY);
            newY = postItStartY + deltaY;
        }
        
        // Actualizar la acción en el historial
        const history = userWhiteboards[currentWhiteboardMode].history;
        const actionIndex = history.findIndex(a => a.id === selectedPostItAction.id);
        
        if (actionIndex !== -1) {
            // Actualizar tamaño y posición
            history[actionIndex].x = newX;
            history[actionIndex].y = newY;
            history[actionIndex].width = newWidth;
            history[actionIndex].height = newHeight;
            
            // Redibujar desde el historial actualizado
            redrawFromHistory();
            
            // Enviar acción de redimensionamiento a otros usuarios
            const actionId = `resize_${Date.now()}_${++actionCounter}`;
            const currentUID = getCurrentUID();
            const currentUserName = getCurrentUser();
            const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
            
            const resizeAction = {
                id: actionId,
                type: 'postit_resize',
                originalId: selectedPostItAction.id,
                x: newX,
                y: newY,
                width: newWidth,
                height: newHeight,
                userId: currentUID,
                userName: currentUserName,
                whiteboardMode: currentWhiteboardMode,
                created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico
                created_at_iso: new Date().toISOString()
            };
            
            lastSentActionId = actionId;
            sentActionIds.add(actionId);
            sendDrawingAction(resizeAction);
            
            // Actualizar posición del botón después de redimensionar (para que quede en la posición correcta)
            const updatedPostIt = { ...selectedPostItAction, x: newX, y: newY, width: newWidth, height: newHeight };
            selectedPostItAction = updatedPostIt; // Actualizar la referencia con el nuevo tamaño y posición
            updatePostItDeleteButtonPosition(updatedPostIt);
        }
        
        // NO limpiar la selección aquí - mantener el post-it seleccionado y el botón visible
        // Solo limpiar el estado de redimensionamiento
        isResizingPostIt = false;
        resizeHandle = null;
        postItStartX = 0;
        postItStartY = 0;
        postItStartWidth = 0;
        postItStartHeight = 0;
        // NO llamar hidePostItDeleteButton() - mantener el botón visible
        
        // Restaurar cursor
        if (whiteboardCanvas) {
            if (currentTool === 'move') {
                whiteboardCanvas.style.cursor = 'move';
            } else {
                whiteboardCanvas.style.cursor = 'default';
            }
        }
        
        isDrawing = false;
        return;
    }
    
    // Si estábamos moviendo post-it, actualizar su posición en el historial
    if (isMovingPostIt && selectedPostItAction) {
        const rect = whiteboardCanvas.getBoundingClientRect();
        const endX = e ? (e.clientX - rect.left) : lastX;
        const endY = e ? (e.clientY - rect.top) : lastY;
        
        // Calcular nueva posición
        const newX = endX - postItOffsetX;
        const newY = endY - postItOffsetY;
        
        // Actualizar la acción en el historial
        const history = userWhiteboards[currentWhiteboardMode].history;
        const actionIndex = history.findIndex(a => a.id === selectedPostItAction.id);
        
        if (actionIndex !== -1) {
            // Actualizar posición
            history[actionIndex].x = newX;
            history[actionIndex].y = newY;
            
            // Redibujar desde el historial actualizado
            redrawFromHistory();
            
            // Enviar acción de movimiento a otros usuarios
            const actionId = `move_${Date.now()}_${++actionCounter}`;
            const currentUID = getCurrentUID();
            const currentUserName = getCurrentUser();
            const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
            
            const moveAction = {
                id: actionId,
                type: 'postit_move',
                originalId: selectedPostItAction.id,
                x: newX,
                y: newY,
                userId: currentUID,
                userName: currentUserName,
                whiteboardMode: currentWhiteboardMode,
                created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico
                created_at_iso: new Date().toISOString()
            };
            
            lastSentActionId = actionId;
            sentActionIds.add(actionId);
            sendDrawingAction(moveAction);
            
            // Actualizar posición del botón después de mover (para que quede en la posición final)
            const updatedPostIt = { ...selectedPostItAction, x: newX, y: newY };
            selectedPostItAction = updatedPostIt; // Actualizar la referencia con la nueva posición
            updatePostItDeleteButtonPosition(updatedPostIt);
        }
        
        // NO limpiar la selección aquí - mantener el post-it seleccionado y el botón visible
        // Solo limpiar el estado de movimiento
        isMovingPostIt = false;
        postItOffsetX = 0;
        postItOffsetY = 0;
        // NO llamar hidePostItDeleteButton() - mantener el botón visible
        
        // Restaurar cursor
        if (whiteboardCanvas) {
            if (currentTool === 'move') {
                whiteboardCanvas.style.cursor = 'move';
            } else {
                whiteboardCanvas.style.cursor = 'default';
            }
        }
        
        isDrawing = false;
        return;
    }
    
    // Si estábamos moviendo texto, actualizar su posición en el historial
    if (isMovingText && selectedTextAction) {
        const rect = whiteboardCanvas.getBoundingClientRect();
        const endX = e ? (e.clientX - rect.left) : lastX;
        const endY = e ? (e.clientY - rect.top) : lastY;
        
        // Calcular nueva posición
        const newX = endX - textOffsetX;
        const newY = endY - textOffsetY;
        
        // Actualizar la acción en el historial
        const history = userWhiteboards[currentWhiteboardMode].history;
        const actionIndex = history.findIndex(a => a.id === selectedTextAction.id);
        
        if (actionIndex !== -1) {
            // Actualizar posición
            history[actionIndex].x = newX;
            history[actionIndex].y = newY;
            
            // Redibujar desde el historial actualizado
            redrawFromHistory();
            
            // Enviar acción de movimiento a otros usuarios
            const actionId = `move_${Date.now()}_${++actionCounter}`;
            const currentUID = getCurrentUID();
            const currentUserName = getCurrentUser();
            const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
            
            const moveAction = {
                id: actionId,
                type: 'text_move',
                originalId: selectedTextAction.id,
                x: newX,
                y: newY,
                userId: currentUID,
                userName: currentUserName,
                whiteboardMode: currentWhiteboardMode,
                created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico
                created_at_iso: new Date().toISOString()
            };
            
            lastSentActionId = actionId;
            sentActionIds.add(actionId);
            sendDrawingAction(moveAction);
        }
        
        // Limpiar tiempo de último movimiento
        if (selectedTextAction && selectedTextAction.lastMoveTime) {
            delete selectedTextAction.lastMoveTime;
        }
        
        // Limpiar selección
        selectedTextAction = null;
        isMovingText = false;
        textOffsetX = 0;
        textOffsetY = 0;
        
        // Restaurar cursor
        if (whiteboardCanvas) {
            if (currentTool === 'move') {
                whiteboardCanvas.style.cursor = 'move';
            } else {
                whiteboardCanvas.style.cursor = 'default';
            }
        }
        
        isDrawing = false;
        return;
    }
    
    // Si estábamos dibujando una forma, finalizarla
    if (isDrawingShape && (currentTool === 'line' || currentTool === 'rectangle' || currentTool === 'circle')) {
        const rect = whiteboardCanvas.getBoundingClientRect();
        const endX = e ? (e.clientX - rect.left) : lastX;
        const endY = e ? (e.clientY - rect.top) : lastY;
        
        // Redibujar desde el historial para limpiar la previsualización
        redrawFromHistory();
        
        // Dibujar la forma final
        drawShape(startX, startY, endX, endY);
        
        isDrawingShape = false;
    } else if (isDrawingShape && currentTool === 'text') {
        // Si es texto, crear el input de texto con el tamaño del rectángulo
        const rect = whiteboardCanvas.getBoundingClientRect();
        const endX = e ? (e.clientX - rect.left) : lastX;
        const endY = e ? (e.clientY - rect.top) : lastY;
        
        // Calcular posición y tamaño del rectángulo
        const x = Math.min(startX, endX);
        const y = Math.min(startY, endY);
        const width = Math.abs(endX - startX);
        const height = Math.abs(endY - startY);
        
        // Solo crear el input si el rectángulo tiene un tamaño mínimo
        if (width > 10 && height > 10) {
            // Redibujar desde el historial para limpiar la previsualización
            redrawFromHistory();
            
            // Crear el input de texto con el tamaño del rectángulo
            addTextAtPosition(x, y, width, height);
        }
        
        isDrawingShape = false;
    } else if (isDrawingShape && currentTool === 'postit') {
        // Si es post-it, crear el input de texto con el tamaño del rectángulo
        const rect = whiteboardCanvas.getBoundingClientRect();
        const endX = e ? (e.clientX - rect.left) : lastX;
        const endY = e ? (e.clientY - rect.top) : lastY;
        
        // Calcular posición y tamaño del rectángulo
        const x = Math.min(startX, endX);
        const y = Math.min(startY, endY);
        const width = Math.abs(endX - startX);
        const height = Math.abs(endY - startY);
        
        // Solo crear el input si el rectángulo tiene un tamaño mínimo
        if (width > 10 && height > 10) {
            // Redibujar desde el historial para limpiar la previsualización
            redrawFromHistory();
            
            // Crear el input de post-it con el tamaño del rectángulo
            addPostItAtPosition(x, y, width, height);
        }
        
        isDrawingShape = false;
    }
    
    isDrawing = false;
}

// Manejar toque (móvil)
function handleTouchStart(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousedown', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    whiteboardCanvas.dispatchEvent(mouseEvent);
}

function handleTouchMove(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    whiteboardCanvas.dispatchEvent(mouseEvent);
}

function handleTouchEnd(e) {
    e.preventDefault();
    const mouseEvent = new MouseEvent('mouseup', {});
    whiteboardCanvas.dispatchEvent(mouseEvent);
}

// Guardar en historial
function saveToHistory(action) {
    // LOG ESPECÍFICO PARA BORRADO
    if (action.tool === 'eraser' || action.type === 'clear') {
        console.log('[Whiteboard] 💾 GUARDANDO EN HISTORIAL (BORRADO):', {
            actionId: action.id,
            type: action.type,
            tool: action.tool,
            whiteboardMode: action.whiteboardMode || currentWhiteboardMode,
            userId: action.userId,
            userName: action.userName,
            historyLengthBefore: userWhiteboards[currentWhiteboardMode] ? userWhiteboards[currentWhiteboardMode].history.length : 0
        });
    }
    
    // Guardar en el historial de la pizarra actual
    if (!userWhiteboards[currentWhiteboardMode]) {
        initializeUserWhiteboard(currentWhiteboardMode);
    }
    
    const currentBoard = userWhiteboards[currentWhiteboardMode];
    currentBoard.history.push(action);
    historyIndex = currentBoard.history.length - 1;
    
    // También actualizar drawingHistory para compatibilidad
    drawingHistory = currentBoard.history;
    
    // Limitar historial a 1000 acciones
    if (drawingHistory.length > 1000) {
        drawingHistory.shift();
        historyIndex--;
    }
    
    // LOG DESPUÉS DE GUARDAR
    if (action.tool === 'eraser' || action.type === 'clear') {
        console.log('[Whiteboard] ✅ GUARDADO EN HISTORIAL (BORRADO):', {
            actionId: action.id,
            historyLengthAfter: currentBoard.history.length,
            totalEraserActions: currentBoard.history.filter(a => a.tool === 'eraser' || a.type === 'clear').length
        });
    }
}

// Redibujar desde historial
function redrawFromHistory() {
    if (!whiteboardCtx || !whiteboardCanvas) {
        console.log('[Whiteboard] ⚠️ No se puede redibujar: canvas no inicializado');
        return;
    }
    
    // Limpiar canvas
    whiteboardCtx.clearRect(0, 0, whiteboardCanvas.width, whiteboardCanvas.height);
    
    // Obtener historial de la pizarra actual
    if (!userWhiteboards[currentWhiteboardMode]) {
        initializeUserWhiteboard(currentWhiteboardMode);
    }
    
    const currentBoard = userWhiteboards[currentWhiteboardMode];
    let historyToDraw = [...currentBoard.history]; // Crear copia para no modificar el original
    
    // CRÍTICO: Ordenar el historial por timestamp ANTES de redibujar
    // Esto asegura que las acciones de borrado se apliquen en el orden cronológico correcto
    historyToDraw.sort((a, b) => {
        // Función auxiliar para extraer timestamp cronológico
        const getTimestamp = (action) => {
            // Prioridad 1: created_at del mensaje (MÁS CONFIABLE para orden cronológico)
            // Este es el timestamp real de cuándo se creó el mensaje en la BD
            if (action.created_at) {
                const ts = typeof action.created_at === 'number' 
                    ? action.created_at 
                    : new Date(action.created_at).getTime();
                if (!isNaN(ts)) return ts;
            }
            
            // Prioridad 2: messageId (puede no ser cronológico, pero es mejor que nada)
            if (action.messageId) {
                const ts = parseInt(action.messageId);
                if (!isNaN(ts)) return ts;
            }
            
            // Prioridad 3: ID de acción (formato: action_timestamp_counter o resize_timestamp_counter, etc.)
            if (action.id) {
                const parts = action.id.split('_');
                if (parts.length >= 2) {
                    const ts = parseInt(parts[1]);
                    if (!isNaN(ts)) return ts;
                }
                // Si el ID no tiene formato timestamp, intentar parsearlo directamente
                const directTs = parseInt(action.id);
                if (!isNaN(directTs)) return directTs;
            }
            
            // Prioridad 4: timestamp directo
            if (action.timestamp) {
                const ts = typeof action.timestamp === 'number' 
                    ? action.timestamp 
                    : parseInt(action.timestamp);
                if (!isNaN(ts)) return ts;
            }
            
            // Fallback: usar 0 para acciones sin timestamp (se colocarán al inicio)
            return 0;
        };
        
        const tsA = getTimestamp(a);
        const tsB = getTimestamp(b);
        
        // Si tienen el mismo timestamp, mantener el orden original (estable)
        if (tsA === tsB) {
            return 0;
        }
        
        return tsA - tsB; // Orden ascendente (más antiguas primero)
    });
    
    // LOG para verificar el ordenamiento
    if (historyToDraw.length > 0) {
        const firstAction = historyToDraw[0];
        const lastAction = historyToDraw[historyToDraw.length - 1];
        
        // Función auxiliar para obtener timestamp para logs
        const getTimestampForLog = (act) => {
            if (act.created_at) return act.created_at;
            if (act.messageId) return act.messageId;
            if (act.id) {
                const parts = act.id.split('_');
                if (parts.length >= 2) return parts[1];
            }
            return 'unknown';
        };
        
        const firstTs = getTimestampForLog(firstAction);
        const lastTs = getTimestampForLog(lastAction);
        
        console.log('[Whiteboard] 📊 ORDENAMIENTO CRONOLÓGICO:', {
            totalActions: historyToDraw.length,
            firstActionTimestamp: firstTs,
            lastActionTimestamp: lastTs,
            firstActionType: firstAction.type,
            lastActionType: lastAction.type,
            firstActionHasCreatedAt: !!firstAction.created_at,
            lastActionHasCreatedAt: !!lastAction.created_at,
            firstActionTool: firstAction.tool || 'N/A',
            lastActionTool: lastAction.tool || 'N/A'
        });
    }
    
    drawingHistory = historyToDraw; // Sincronizar para compatibilidad
    
    // Log reducido - solo cuando hay muchas acciones Y solo una vez cada 100 redibujados
    if (historyToDraw.length > 50) {
        if (!window._redrawCount) window._redrawCount = 0;
        window._redrawCount++;
        if (window._redrawCount % 100 === 0) {
            console.log('[Whiteboard] 🎨 Redibujando pizarra:', {
                mode: currentWhiteboardMode,
                totalActions: historyToDraw.length,
                redrawCount: window._redrawCount
            });
        }
    }
    
    // Contar acciones de borrado antes de redibujar
    const eraserActionsCount = historyToDraw.filter(a => a.tool === 'eraser' || a.type === 'clear').length;
    if (eraserActionsCount > 0) {
        console.log('[Whiteboard] 🔄 REDIBUJANDO CON BORRADOS (ORDENADOS CRONOLÓGICAMENTE):', {
            totalActions: historyToDraw.length,
            eraserActions: eraserActionsCount,
            clearActions: historyToDraw.filter(a => a.type === 'clear').length,
            whiteboardMode: currentWhiteboardMode,
            isSorted: true
        });
    }
    
    // Redibujar todas las acciones en orden cronológico
    let eraserAppliedCount = 0;
    const logInterval = Math.max(1, Math.floor(eraserActionsCount / 10)); // Log cada 10% aproximadamente
    historyToDraw.forEach((action, index) => {
        if (action.type === 'draw') {
            // LOG reducido para acciones de borrado durante redibujo (solo cada 10% o al inicio/fin)
            if (action.tool === 'eraser') {
                eraserAppliedCount++;
                // Solo loguear en intervalos o al inicio/fin para evitar spam
                if (eraserAppliedCount === 1 || 
                    eraserAppliedCount === eraserActionsCount || 
                    (logInterval > 0 && eraserAppliedCount % logInterval === 0)) {
                    console.log(`[Whiteboard] 🧹 REDIBUJANDO BORRADO ${eraserAppliedCount}/${eraserActionsCount}${eraserAppliedCount === eraserActionsCount ? ' (completado)' : ''}`);
                }
            }
            
            whiteboardCtx.beginPath();
            whiteboardCtx.moveTo(action.fromX, action.fromY);
            whiteboardCtx.lineTo(action.toX, action.toY);
            
            if (action.tool === 'pen') {
                whiteboardCtx.strokeStyle = action.color;
                whiteboardCtx.globalCompositeOperation = 'source-over';
                whiteboardCtx.lineWidth = action.lineWidth;
            } else if (action.tool === 'eraser') {
                whiteboardCtx.strokeStyle = '#ffffff';
                whiteboardCtx.globalCompositeOperation = 'destination-out';
                // CRÍTICO: Multiplicar por 2 para mantener consistencia con el borrado local
                // El borrador local usa lineWidth * 2, así que debemos hacer lo mismo aquí
                whiteboardCtx.lineWidth = action.lineWidth * 2;
            }
            whiteboardCtx.lineCap = 'round';
            whiteboardCtx.lineJoin = 'round';
            whiteboardCtx.stroke();
            
            if (action.tool === 'eraser') {
                whiteboardCtx.globalCompositeOperation = 'source-over';
            }
        } else if (action.type === 'shape') {
            whiteboardCtx.strokeStyle = action.color;
            whiteboardCtx.lineWidth = action.lineWidth;
            whiteboardCtx.globalCompositeOperation = 'source-over';
            
            if (action.tool === 'line') {
                whiteboardCtx.beginPath();
                whiteboardCtx.moveTo(action.fromX, action.fromY);
                whiteboardCtx.lineTo(action.toX, action.toY);
                whiteboardCtx.stroke();
            } else if (action.tool === 'rectangle') {
                whiteboardCtx.strokeRect(action.x, action.y, action.width, action.height);
            } else if (action.tool === 'circle') {
                whiteboardCtx.beginPath();
                whiteboardCtx.arc(action.centerX, action.centerY, action.radius, 0, 2 * Math.PI);
                whiteboardCtx.stroke();
            }
        } else if (action.type === 'text') {
            whiteboardCtx.fillStyle = action.color;
            const fontSize = action.fontSize || 16;
            const fontFamily = action.fontFamily || 'Arial';
            whiteboardCtx.font = `${fontSize}px ${fontFamily}`;
            
            // Si hay ancho y alto, dibujar con word wrap
            if (action.width && action.height) {
                const lines = wrapText(action.text, action.width - 16, fontSize, fontFamily);
                const lineHeight = fontSize * 1.2;
                const startY = action.y + fontSize + 4;
                
                lines.forEach((line, index) => {
                    const lineY = startY + (index * lineHeight);
                    if (lineY <= action.y + action.height - 4) {
                        whiteboardCtx.fillText(line, action.x + 8, lineY);
                    }
                });
            } else {
                whiteboardCtx.fillText(action.text, action.x, action.y);
            }
        } else if (action.type === 'postit') {
            drawPostIt(action);
        } else if (action.type === 'clear') {
            // CRÍTICO: Las acciones de clear deben aplicarse en el orden cronológico correcto
            // Si hay dibujos después del clear, el clear solo debe borrar lo que había antes
            // Por eso es importante que el historial esté ordenado cronológicamente
            console.log('[Whiteboard] 🧹 REDIBUJANDO CLEAR:', {
                actionId: action.id,
                index: index,
                totalActions: historyToDraw.length,
                actionsAfterClear: historyToDraw.length - index - 1,
                whiteboardMode: currentWhiteboardMode,
                timestamp: action.id ? action.id.split('_')[1] : (action.messageId || 'unknown')
            });
            // Limpiar el canvas - esto borra todo lo dibujado hasta este punto
            // Si hay acciones después de este clear, se dibujarán después
            whiteboardCtx.clearRect(0, 0, whiteboardCanvas.width, whiteboardCanvas.height);
        }
    });
    
    // LOG final después de redibujar
    if (eraserActionsCount > 0) {
        console.log('[Whiteboard] ✅ REDIBUJO COMPLETADO:', {
            totalActions: historyToDraw.length,
            eraserActionsApplied: eraserAppliedCount,
            clearActions: historyToDraw.filter(a => a.type === 'clear').length
        });
    }
}

// Set para rastrear acciones ya procesadas (evitar bucles infinitos)
const processedActions = new Set();

// Aplicar acción de dibujo recibida (de otros usuarios)
function applyDrawingAction(action) {
    // Crear un ID único para esta acción
    // Prioridad: messageId > id > generado basado en contenido
    let actionKey;
    if (action.messageId) {
        // Usar messageId del chat para máxima consistencia
        actionKey = `msg_${action.messageId}`;
    } else if (action.id) {
        // Usar id de la acción si existe
        actionKey = `action_${action.id}`;
    } else {
        // Generar basado en contenido (menos confiable pero mejor que nada)
        actionKey = `${action.type}_${action.fromX}_${action.fromY}_${action.toX}_${action.toY}_${action.userId || 'unknown'}_${Date.parse(action.timestamp) || Date.now()}`;
    }
    
    // LOG TEMPORAL PARA DEBUGGING
    const currentUID = getCurrentUID();
    const isOurAction = action.id && (action.id === lastSentActionId || sentActionIds.has(action.id));
    
    // Verificar si es una acción nueva o antigua basándose en el timestamp
    const actionTimestamp = action.id ? parseInt(action.id.split('_')[1]) : 0;
    const currentTime = Date.now();
    const timeDiff = currentTime - actionTimestamp;
    const isRecentAction = timeDiff < 5000; // Acción de los últimos 5 segundos
    
    // Log eliminado para mejorar rendimiento - solo loggear en modo debug si es necesario
    // console.log('[Whiteboard] 🔵 applyDrawingAction LLAMADO:', {...});
    
    // Evitar procesar la misma acción múltiples veces (previene bucles infinitos)
    // IMPORTANTE: Solo verificar si la acción ya fue aplicada exitosamente al canvas
    // No marcar como procesada hasta que se haya aplicado realmente
    if (processedActions.has(actionKey)) {
        // Silenciosamente ignorar acciones ya procesadas (sin log para evitar spam y mejorar rendimiento)
        return;
    }
    
    // Limpiar acciones muy antiguas si el Set crece demasiado (más de 1000)
    if (processedActions.size > 1000) {
        processedActions.clear();
        console.log('[Whiteboard] 🧹 Limpiando cache de acciones procesadas');
    }
    
    // NO marcar como procesada todavía - solo después de aplicarla exitosamente
    
    // Evitar procesar nuestras propias acciones (ya las dibujamos localmente)
    // EXCEPTO para text_move y text_edit que se manejan de forma especial más adelante
    if (action.type !== 'text_move' && action.type !== 'text_edit' && action.id && (action.id === lastSentActionId || sentActionIds.has(action.id))) {
        // Es nuestra propia acción, no procesarla (sin log para mejorar rendimiento)
        return;
    }
    
    // Determinar en qué pizarra aplicar la acción
    const targetMode = action.whiteboardMode || 'general';
    
    // Inicializar la pizarra objetivo si no existe
    if (!userWhiteboards[targetMode]) {
        initializeUserWhiteboard(targetMode);
    }
    
    // Verificar si la acción ya existe en el historial antes de agregarla
    // Para text_move y postit_move, no agregar al historial (solo actualizar la posición)
    if (action.type === 'text_move') {
        // Para text_move, buscar el texto original y actualizar su posición
        const history = userWhiteboards[targetMode].history;
        const textIndex = history.findIndex(a => a.id === action.originalId);
        if (textIndex !== -1) {
            // Actualizar posición del texto existente
            history[textIndex].x = action.x;
            history[textIndex].y = action.y;
            
            // Redibujar si estamos en la pizarra correcta para ver el movimiento en tiempo real
            if (targetMode === currentWhiteboardMode && whiteboardCtx && whiteboardCanvas) {
                redrawFromHistory();
            }
        }
        // CRÍTICO: Marcar como procesada y NO agregar text_move al historial (solo actualizar el texto existente)
        processedActions.add(actionKey);
        return;
    } else if (action.type === 'text_edit') {
        // Para text_edit, buscar el texto original y actualizar su contenido
        const history = userWhiteboards[targetMode].history;
        const textIndex = history.findIndex(a => a.id === action.originalId);
        if (textIndex !== -1) {
            // Actualizar el texto
            history[textIndex].text = action.text;
            
            // Redibujar si estamos en la pizarra correcta para ver la edición en tiempo real
            if (targetMode === currentWhiteboardMode && whiteboardCtx && whiteboardCanvas) {
                redrawFromHistory();
            }
        }
        // CRÍTICO: Marcar como procesada y NO agregar text_edit al historial (solo actualizar el texto existente)
        processedActions.add(actionKey);
        return;
    } else if (action.type === 'postit_move') {
        // Para postit_move, buscar el post-it original y actualizar su posición
        const history = userWhiteboards[targetMode].history;
        const postItIndex = history.findIndex(a => a.id === action.originalId);
        if (postItIndex !== -1) {
            // Actualizar posición del post-it existente
            history[postItIndex].x = action.x;
            history[postItIndex].y = action.y;
            
            // Redibujar si estamos en la pizarra correcta para ver el movimiento en tiempo real
            if (targetMode === currentWhiteboardMode && whiteboardCtx && whiteboardCanvas) {
                redrawFromHistory();
            }
        }
        // No agregar postit_move al historial (solo actualizar el post-it existente)
    } else if (action.type === 'postit_resize') {
        // Para postit_resize, buscar el post-it original y actualizar su tamaño y posición
        const history = userWhiteboards[targetMode].history;
        const postItIndex = history.findIndex(a => a.id === action.originalId);
        if (postItIndex !== -1) {
            // Actualizar tamaño y posición del post-it existente
            history[postItIndex].x = action.x;
            history[postItIndex].y = action.y;
            history[postItIndex].width = action.width;
            history[postItIndex].height = action.height;
            
            // Redibujar si estamos en la pizarra correcta para ver el redimensionamiento en tiempo real
            if (targetMode === currentWhiteboardMode && whiteboardCtx && whiteboardCanvas) {
                redrawFromHistory();
            }
        }
        // No agregar postit_resize al historial (solo actualizar el post-it existente)
    } else if (action.type === 'postit_delete') {
        // Para postit_delete, eliminar el post-it del historial
        const history = userWhiteboards[targetMode].history;
        const postItIndex = history.findIndex(a => a.id === action.originalId);
        if (postItIndex !== -1) {
            // Eliminar el post-it del historial
            history.splice(postItIndex, 1);
            console.log('[Whiteboard] 🗑️ Post-it eliminado del historial (acción remota):', {
                originalId: action.originalId,
                actionId: action.id,
                fromUser: action.userName || action.userId,
                remainingPostIts: history.filter(a => a.type === 'postit').length
            });
            
            // Redibujar si estamos en la pizarra correcta
            if (targetMode === currentWhiteboardMode && whiteboardCtx && whiteboardCanvas) {
                redrawFromHistory();
            }
        }
        // No agregar postit_delete al historial (solo eliminar el post-it existente)
    } else {
        // Para otras acciones, verificar si ya existe
        const existsInHistory = userWhiteboards[targetMode].history.some(a => {
            // Verificar por messageId o id primero (más confiable)
            if (action.messageId && a.messageId === action.messageId) return true;
            if (action.id && a.id === action.id) return true;
            
            // Para acciones de texto, comparar por tipo, posición, texto y usuario
            // IMPORTANTE: Si la acción tiene originalId, es un movimiento/edición, no crear nueva acción
            if (action.type === 'text' && a.type === 'text') {
                // Si tiene originalId, es un movimiento/edición, verificar por ID original
                if (action.originalId && a.id === action.originalId) {
                    return true; // Es el mismo texto, solo movido/editado
                }
                // Si no tiene originalId, comparar por posición, texto y usuario
                return a.x === action.x && 
                       a.y === action.y && 
                       a.text === action.text && 
                       a.userId === action.userId;
            }
            
            // Para acciones de post-it, comparar por ID primero (más confiable)
            if (action.type === 'postit' && a.type === 'postit') {
                // Si tienen el mismo ID, es la misma acción
                if (action.id && a.id === action.id) return true;
                // Si tienen el mismo messageId, es la misma acción
                if (action.messageId && a.messageId === action.messageId) return true;
                // Comparar por tipo, posición, texto y usuario (menos confiable)
                return a.x === action.x && 
                       a.y === action.y && 
                       a.text === action.text && 
                       a.userId === action.userId;
            }
            
            // Para otras acciones (dibujo, formas), comparar por coordenadas
            if (a.type === action.type && 
                a.fromX === action.fromX && 
                a.fromY === action.fromY && 
                a.toX === action.toX && 
                a.toY === action.toY && 
                a.userId === action.userId) {
                return true;
            }
            
            return false;
        });
        
        // Solo agregar si no existe
        if (!existsInHistory) {
            // IMPORTANTE: Insertar la acción en el orden correcto basado en timestamp cronológico
            // Esto asegura que las acciones de borrado se apliquen en el orden cronológico correcto
            const history = userWhiteboards[targetMode].history;
            
            // Función auxiliar para obtener timestamp cronológico de una acción
            const getActionTimestamp = (act) => {
                // Prioridad 1: created_at (más confiable)
                if (act.created_at) {
                    const ts = typeof act.created_at === 'number' 
                        ? act.created_at 
                        : new Date(act.created_at).getTime();
                    if (!isNaN(ts)) return ts;
                }
                // Prioridad 2: messageId
                if (act.messageId) {
                    const ts = parseInt(act.messageId);
                    if (!isNaN(ts)) return ts;
                }
                // Prioridad 3: ID de acción
                if (act.id) {
                    const parts = act.id.split('_');
                    if (parts.length >= 2) {
                        const ts = parseInt(parts[1]);
                        if (!isNaN(ts)) return ts;
                    }
                }
                return 0;
            };
            
            const actionTimestamp = getActionTimestamp(action);
            
            // Encontrar la posición correcta para insertar (mantener orden cronológico)
            let insertIndex = history.length;
            for (let i = 0; i < history.length; i++) {
                const existingTimestamp = getActionTimestamp(history[i]);
                if (actionTimestamp < existingTimestamp) {
                    insertIndex = i;
                    break;
                }
            }
            
            // Insertar en la posición correcta
            history.splice(insertIndex, 0, action);
            
            // LOG ESPECÍFICO para acciones de borrado insertadas en historial
            if (action.tool === 'eraser' || action.type === 'clear') {
                console.log('[Whiteboard] 💾 BORRADO INSERTADO EN HISTORIAL (orden cronológico):', {
                    actionId: action.id,
                    timestamp: actionTimestamp,
                    insertIndex: insertIndex,
                    totalHistoryLength: history.length,
                    whiteboardMode: targetMode
                });
            }
        }
    }
    
    // Verificar si el canvas está listo
    const canvasElement = document.getElementById('whiteboard-canvas');
    
    // Si la pizarra está abierta, forzar la inicialización del canvas si es necesario
    if (isWhiteboardOpen && canvasElement) {
        // Si el canvas no está inicializado, inicializarlo INMEDIATAMENTE
        if (!whiteboardCanvas || !whiteboardCtx) {
            console.log('[Whiteboard] ⚠️ Pizarra abierta pero canvas no inicializado, inicializando...');
            initializeWhiteboard();
            // Después de inicializar, verificar que se inicializó correctamente
            if (!whiteboardCanvas || !whiteboardCtx) {
                // Si aún no está inicializado, intentar de nuevo
                setTimeout(() => {
                    initializeWhiteboard();
                }, 10);
            }
        }
    }
    
    // Verificar si el canvas está listo DESPUÉS de intentar inicializarlo
    // Verificar el estado de la pizarra de forma más robusta: usar el DOM como fuente de verdad
    const whiteboardPanel = document.getElementById('whiteboard-panel');
    
    // Verificar de múltiples formas si la pizarra está abierta:
    // 1. Variable JavaScript
    // 2. Clase CSS 'open'
    // 3. Transform del panel (si está visible)
    const panelHasOpenClass = whiteboardPanel && whiteboardPanel.classList.contains('open');
    
    // Verificar también si el panel está visible usando getComputedStyle
    let panelIsVisible = false;
    if (whiteboardPanel) {
        try {
            const computedStyle = window.getComputedStyle(whiteboardPanel);
            const transform = computedStyle.transform;
            // Si el transform no es 'none' y no es la matriz identidad, el panel está visible
            panelIsVisible = transform !== 'none' && transform !== 'matrix(1, 0, 0, 1, 0, 0)';
            // También verificar si el transform contiene translateY(0) o translateY(0px)
            if (transform.includes('translateY(0') || transform.includes('translateY(0px)')) {
                panelIsVisible = true;
            }
        } catch (e) {
            // Si hay error al obtener el estilo, usar solo la clase
            panelIsVisible = false;
        }
    }
    
    const panelIsOpen = panelHasOpenClass || panelIsVisible;
    
    // Usar la variable JavaScript O el estado del DOM - priorizar DOM porque es más confiable
    // IMPORTANTE: Usar panelIsOpen (que incluye panelIsVisible) en lugar de solo panelHasOpenClass
    const wbIsOpen = panelIsOpen || isWhiteboardOpen;
    
    // Logs eliminados para mejorar rendimiento - demasiado overhead en cada acción
    // Solo loggear errores o casos críticos
    
    let isCanvasReady = false;
    
    if (wbIsOpen && canvasElement) {
        // Si tenemos el elemento del canvas, verificar si está inicializado
        if (whiteboardCanvas && whiteboardCtx) {
            // Verificar que el canvas tenga dimensiones válidas
            if (whiteboardCanvas.width > 0 && whiteboardCanvas.height > 0) {
                isCanvasReady = true;
                // Log eliminado para mejorar rendimiento
            } else {
                // El canvas no tiene dimensiones válidas, redimensionar
                resizeCanvas();
                if (whiteboardCanvas.width > 0 && whiteboardCanvas.height > 0) {
                    isCanvasReady = true;
                    // Log eliminado para mejorar rendimiento
                }
            }
        } else {
            // Si no está inicializado pero el elemento existe, inicializar INMEDIATAMENTE
            console.log('[Whiteboard] ⚠️ Canvas no inicializado, inicializando...');
            const initialized = initializeWhiteboard();
            if (initialized && whiteboardCanvas && whiteboardCtx) {
                // Verificar dimensiones después de inicializar
                if (whiteboardCanvas.width > 0 && whiteboardCanvas.height > 0) {
                    isCanvasReady = true;
                    console.log('[Whiteboard] ✅ Canvas inicializado:', {
                        width: whiteboardCanvas.width,
                        height: whiteboardCanvas.height
                    });
                } else {
                    // Redimensionar si no tiene dimensiones
                    resizeCanvas();
                    if (whiteboardCanvas.width > 0 && whiteboardCanvas.height > 0) {
                        isCanvasReady = true;
                        console.log('[Whiteboard] ✅ Canvas inicializado y redimensionado');
                    }
                }
            } else {
                console.log('[Whiteboard] ❌ No se pudo inicializar el canvas');
            }
        }
    } else {
        console.log('[Whiteboard] ⚠️ Pizarra cerrada o sin elemento canvas:');
        console.log('  - wbIsOpen:', wbIsOpen);
        console.log('  - hasCanvasElement:', !!canvasElement);
        console.log('  - isWhiteboardOpen:', isWhiteboardOpen);
        console.log('  - panelHasOpenClass:', panelHasOpenClass);
        console.log('  - panelIsOpen:', panelIsOpen);
    }
    
    // Si el canvas no está listo, pero la pizarra está abierta, intentar aplicar la acción
    // Esto es crítico para el tiempo real: si la pizarra está abierta, debemos intentar aplicar la acción
    if (!isCanvasReady) {
        console.log('[Whiteboard] ⚠️ Canvas no listo, pero intentando aplicar acción...');
        
        // Si la pizarra está abierta (según el DOM o la variable), intentar aplicar la acción
        // IMPORTANTE: Usar panelIsOpen (que incluye panelIsVisible) O isWhiteboardOpen como fuente de verdad
        if ((panelIsOpen || isWhiteboardOpen) && canvasElement) {
            console.log('[Whiteboard] 🔄 Pizarra ABIERTA (según DOM o variable), intentando inicializar y aplicar acción...');
            console.log('  - panelIsOpen:', panelIsOpen);
            console.log('  - panelHasOpenClass:', panelHasOpenClass);
            console.log('  - panelIsVisible:', panelIsVisible);
            console.log('  - isWhiteboardOpen:', isWhiteboardOpen);
            console.log('  - hasCanvasElement:', !!canvasElement);
            
            // Intentar inicializar inmediatamente
            if (!whiteboardCanvas || !whiteboardCtx) {
                console.log('[Whiteboard] 🔄 Inicializando canvas...');
                initializeWhiteboard();
            }
            
            // Si el canvas aún no está inicializado, intentar redimensionar
            if (whiteboardCanvas && (!whiteboardCanvas.width || !whiteboardCanvas.height)) {
                console.log('[Whiteboard] 🔄 Redimensionando canvas...');
                resizeCanvas();
            }
            
            // Verificar si ahora está listo DESPUÉS de inicializar
            if (whiteboardCanvas && whiteboardCtx && whiteboardCanvas.width > 0 && whiteboardCanvas.height > 0) {
                console.log('[Whiteboard] ✅ Canvas ahora listo después de inicializar, aplicando acción inmediatamente');
                console.log('  - canvasWidth:', whiteboardCanvas.width);
                console.log('  - canvasHeight:', whiteboardCanvas.height);
                console.log('  - targetMode:', targetMode);
                console.log('  - currentWhiteboardMode:', currentWhiteboardMode);
                
                // El canvas está listo, aplicar la acción AHORA
                if (targetMode === currentWhiteboardMode) {
                    if (action.type === 'draw') {
                        console.log('[Whiteboard] ✅ DIBUJANDO acción en canvas (retry inmediato):', action.id);
                        whiteboardCtx.beginPath();
                        whiteboardCtx.moveTo(action.fromX, action.fromY);
                        whiteboardCtx.lineTo(action.toX, action.toY);
                        
                        if (action.tool === 'pen') {
                            whiteboardCtx.strokeStyle = action.color;
                            whiteboardCtx.globalCompositeOperation = 'source-over';
                        } else if (action.tool === 'eraser') {
                            whiteboardCtx.strokeStyle = '#ffffff';
                            whiteboardCtx.globalCompositeOperation = 'destination-out';
                        }
                        
                        whiteboardCtx.lineWidth = action.lineWidth;
                        whiteboardCtx.lineCap = 'round';
                        whiteboardCtx.lineJoin = 'round';
                        whiteboardCtx.stroke();
                        
                        if (action.tool === 'eraser') {
                            whiteboardCtx.globalCompositeOperation = 'source-over';
                        }
                        console.log('[Whiteboard] ✅ Acción aplicada exitosamente en retry inmediato');
                        // Marcar como procesada SOLO después de aplicarla exitosamente
                        processedActions.add(actionKey);
                    } else if (action.type === 'shape') {
                        // Aplicar forma (línea, rectángulo, círculo)
                        whiteboardCtx.strokeStyle = action.color;
                        whiteboardCtx.lineWidth = action.lineWidth;
                        whiteboardCtx.globalCompositeOperation = 'source-over';
                        
                        if (action.tool === 'line') {
                            whiteboardCtx.beginPath();
                            whiteboardCtx.moveTo(action.fromX, action.fromY);
                            whiteboardCtx.lineTo(action.toX, action.toY);
                            whiteboardCtx.stroke();
                        } else if (action.tool === 'rectangle') {
                            whiteboardCtx.strokeRect(action.x, action.y, action.width, action.height);
                        } else if (action.tool === 'circle') {
                            whiteboardCtx.beginPath();
                            whiteboardCtx.arc(action.centerX, action.centerY, action.radius, 0, 2 * Math.PI);
                            whiteboardCtx.stroke();
                        }
                        processedActions.add(actionKey);
                    } else if (action.type === 'text') {
                        // Aplicar texto (con soporte para word wrap si hay width/height)
                        whiteboardCtx.fillStyle = action.color;
                        const fontSize = action.fontSize || 16;
                        const fontFamily = action.fontFamily || 'Arial';
                        whiteboardCtx.font = `${fontSize}px ${fontFamily}`;
                        
                        // Si hay ancho y alto, dibujar con word wrap
                        if (action.width && action.height) {
                            const lines = wrapText(action.text, action.width - 16, fontSize, fontFamily);
                            const lineHeight = fontSize * 1.2;
                            const startY = action.y + fontSize + 4;
                            
                            lines.forEach((line, index) => {
                                const lineY = startY + (index * lineHeight);
                                if (lineY <= action.y + action.height - 4) {
                                    whiteboardCtx.fillText(line, action.x + 8, lineY);
                                }
                            });
                        } else {
                            // Comportamiento original: una sola línea
                            whiteboardCtx.fillText(action.text, action.x, action.y);
                        }
                        processedActions.add(actionKey);
                    } else if (action.type === 'postit') {
                        // IMPORTANTE: Asegurarse de que el post-it esté en el historial antes de dibujarlo
                        // Esto es crítico porque drawPostIt no guarda en el historial si ya tiene una acción
                        const history = userWhiteboards[targetMode].history;
                        const existsInHistory = history.some(a => {
                            if (a.id === action.id) return true;
                            if (action.messageId && a.messageId === action.messageId) return true;
                            return false;
                        });
                        
                        if (!existsInHistory) {
                            // Guardar en el historial antes de dibujar
                            history.push(action);
                            console.log('[Whiteboard] 📥 Post-it recibido y guardado en historial:', {
                                id: action.id,
                                text: action.text ? action.text.substring(0, 20) + '...' : 'sin texto',
                                mode: targetMode,
                                historyLength: history.length
                            });
                        }
                        
                        // Dibujar post-it
                        drawPostIt(action);
                        processedActions.add(actionKey);
                        
                        // NO redibujar aquí porque drawPostIt ya dibujó el post-it
                        // Redibujar causaría un bucle infinito
                    } else if (action.type === 'text_move') {
                        // Actualizar posición del texto inmediatamente
                        const history = userWhiteboards[targetMode].history;
                        const textIndex = history.findIndex(a => a.id === action.originalId);
                        if (textIndex !== -1) {
                            history[textIndex].x = action.x;
                            history[textIndex].y = action.y;
                            // Redibujar inmediatamente para ver el movimiento en tiempo real
                            redrawFromHistory();
                        }
                        processedActions.add(actionKey);
                    } else if (action.type === 'postit_move') {
                        // Actualizar posición del post-it inmediatamente
                        const history = userWhiteboards[targetMode].history;
                        const postItIndex = history.findIndex(a => a.id === action.originalId);
                        if (postItIndex !== -1) {
                            history[postItIndex].x = action.x;
                            history[postItIndex].y = action.y;
                            // Redibujar inmediatamente para ver el movimiento en tiempo real
                            redrawFromHistory();
                        }
                        processedActions.add(actionKey);
                    } else if (action.type === 'postit_resize') {
                        // Actualizar tamaño del post-it inmediatamente
                        const history = userWhiteboards[targetMode].history;
                        const postItIndex = history.findIndex(a => a.id === action.originalId);
                        if (postItIndex !== -1) {
                            history[postItIndex].x = action.x;
                            history[postItIndex].y = action.y;
                            history[postItIndex].width = action.width;
                            history[postItIndex].height = action.height;
                            // Redibujar inmediatamente para ver el redimensionamiento en tiempo real
                            redrawFromHistory();
                        }
                        processedActions.add(actionKey);
                    } else if (action.type === 'clear') {
                        whiteboardCtx.clearRect(0, 0, whiteboardCanvas.width, whiteboardCanvas.height);
                        // Marcar como procesada SOLO después de aplicarla exitosamente
                        processedActions.add(actionKey);
                    }
                } else {
                    console.log('[Whiteboard] ⚠️ Acción para otra pizarra, no aplicando:', {
                        targetMode: targetMode,
                        currentMode: currentWhiteboardMode
                    });
                }
                // La acción se aplicó, salir
                return;
            } else {
                console.log('[Whiteboard] ⚠️ Canvas aún no listo después de inicializar:', {
                    hasCanvas: !!whiteboardCanvas,
                    hasCtx: !!whiteboardCtx,
                    width: whiteboardCanvas ? whiteboardCanvas.width : 0,
                    height: whiteboardCanvas ? whiteboardCanvas.height : 0
                });
            }
            
            // Si aún no está listo, intentar con retry
            let attempts = 0;
            const maxAttempts = 10; // Reducir a 10 intentos (500ms total)
            
            const tryApplyAction = () => {
                attempts++;
                
                // Verificar si el canvas está listo
                let canvasReady = false;
                
                // Si el canvas no está inicializado, intentar inicializarlo
                if (!whiteboardCanvas || !whiteboardCtx) {
                    if (canvasElement) {
                        initializeWhiteboard();
                    }
                }
                
                // Verificar estado de la pizarra de nuevo
                // Recalcular panelIsOpen para verificar si sigue abierto
                const panelStillHasOpenClass = whiteboardPanel && whiteboardPanel.classList.contains('open');
                let panelStillVisible = false;
                if (whiteboardPanel) {
                    try {
                        const computedStyle = window.getComputedStyle(whiteboardPanel);
                        const transform = computedStyle.transform;
                        panelStillVisible = transform !== 'none' && transform !== 'matrix(1, 0, 0, 1, 0, 0)';
                        if (transform.includes('translateY(0') || transform.includes('translateY(0px)')) {
                            panelStillVisible = true;
                        }
                    } catch (e) {
                        panelStillVisible = false;
                    }
                }
                const panelStillOpen = panelStillHasOpenClass || panelStillVisible;
                const wbOpen = panelStillOpen || isWhiteboardOpen;
                
                // Verificar si ahora está listo
                if (whiteboardCtx && whiteboardCanvas && canvasElement && wbOpen) {
                    // Verificar dimensiones
                    if (whiteboardCanvas.width > 0 && whiteboardCanvas.height > 0) {
                        canvasReady = true;
                    } else {
                        resizeCanvas();
                        if (whiteboardCanvas.width > 0 && whiteboardCanvas.height > 0) {
                            canvasReady = true;
                        }
                    }
                }
                
                if (canvasReady && targetMode === currentWhiteboardMode) {
                    console.log('[Whiteboard] ✅ Canvas listo en intento', attempts, ', aplicando acción');
                    // Aplicar la acción directamente en el canvas
                    if (action.type === 'draw') {
                        whiteboardCtx.beginPath();
                        whiteboardCtx.moveTo(action.fromX, action.fromY);
                        whiteboardCtx.lineTo(action.toX, action.toY);
                        
                        if (action.tool === 'pen') {
                            whiteboardCtx.strokeStyle = action.color;
                            whiteboardCtx.globalCompositeOperation = 'source-over';
                        } else if (action.tool === 'eraser') {
                            whiteboardCtx.strokeStyle = '#ffffff';
                            whiteboardCtx.globalCompositeOperation = 'destination-out';
                        }
                        
                        whiteboardCtx.lineWidth = action.lineWidth;
                        whiteboardCtx.lineCap = 'round';
                        whiteboardCtx.lineJoin = 'round';
                        whiteboardCtx.stroke();
                        
                        if (action.tool === 'eraser') {
                            whiteboardCtx.globalCompositeOperation = 'source-over';
                        }
                        console.log('[Whiteboard] ✅ Acción aplicada en retry exitosamente');
                        // Marcar como procesada SOLO después de aplicarla exitosamente
                        processedActions.add(actionKey);
                    } else if (action.type === 'shape') {
                        whiteboardCtx.strokeStyle = action.color;
                        whiteboardCtx.lineWidth = action.lineWidth;
                        whiteboardCtx.globalCompositeOperation = 'source-over';
                        
                        if (action.tool === 'line') {
                            whiteboardCtx.beginPath();
                            whiteboardCtx.moveTo(action.fromX, action.fromY);
                            whiteboardCtx.lineTo(action.toX, action.toY);
                            whiteboardCtx.stroke();
                        } else if (action.tool === 'rectangle') {
                            whiteboardCtx.strokeRect(action.x, action.y, action.width, action.height);
                        } else if (action.tool === 'circle') {
                            whiteboardCtx.beginPath();
                            whiteboardCtx.arc(action.centerX, action.centerY, action.radius, 0, 2 * Math.PI);
                            whiteboardCtx.stroke();
                        }
                        processedActions.add(actionKey);
                    } else if (action.type === 'text') {
                        whiteboardCtx.fillStyle = action.color;
                        const fontSize = action.fontSize || 16;
                        const fontFamily = action.fontFamily || 'Arial';
                        whiteboardCtx.font = `${fontSize}px ${fontFamily}`;
                        
                        // Si hay ancho y alto, dibujar con word wrap
                        if (action.width && action.height) {
                            const lines = wrapText(action.text, action.width - 16, fontSize, fontFamily);
                            const lineHeight = fontSize * 1.2;
                            const startY = action.y + fontSize + 4;
                            
                            lines.forEach((line, index) => {
                                const lineY = startY + (index * lineHeight);
                                if (lineY <= action.y + action.height - 4) {
                                    whiteboardCtx.fillText(line, action.x + 8, lineY);
                                }
                            });
                        } else {
                            whiteboardCtx.fillText(action.text, action.x, action.y);
                        }
                        processedActions.add(actionKey);
                    } else if (action.type === 'postit') {
                        // IMPORTANTE: Asegurarse de que el post-it esté en el historial antes de dibujarlo
                        // Esto es crítico porque drawPostIt no guarda en el historial si ya tiene una acción
                        const history = userWhiteboards[targetMode].history;
                        const existsInHistory = history.some(a => {
                            if (a.id === action.id) return true;
                            if (action.messageId && a.messageId === action.messageId) return true;
                            return false;
                        });
                        
                        if (!existsInHistory) {
                            // Guardar en el historial antes de dibujar
                            history.push(action);
                            console.log('[Whiteboard] 📥 Post-it recibido y guardado en historial:', {
                                id: action.id,
                                text: action.text ? action.text.substring(0, 20) + '...' : 'sin texto',
                                mode: targetMode,
                                historyLength: history.length
                            });
                        }
                        
                        // Dibujar post-it
                        drawPostIt(action);
                        processedActions.add(actionKey);
                        
                        // NO redibujar aquí porque drawPostIt ya dibujó el post-it
                        // Redibujar causaría un bucle infinito
                    } else if (action.type === 'text_move') {
                        // Actualizar posición del texto inmediatamente
                        const history = userWhiteboards[targetMode].history;
                        const textIndex = history.findIndex(a => a.id === action.originalId);
                        if (textIndex !== -1) {
                            history[textIndex].x = action.x;
                            history[textIndex].y = action.y;
                            // Redibujar inmediatamente para ver el movimiento en tiempo real
                            redrawFromHistory();
                        }
                        processedActions.add(actionKey);
                    } else if (action.type === 'postit_move') {
                        // Actualizar posición del post-it inmediatamente
                        const history = userWhiteboards[targetMode].history;
                        const postItIndex = history.findIndex(a => a.id === action.originalId);
                        if (postItIndex !== -1) {
                            history[postItIndex].x = action.x;
                            history[postItIndex].y = action.y;
                            // Redibujar inmediatamente para ver el movimiento en tiempo real
                            redrawFromHistory();
                        }
                        processedActions.add(actionKey);
                    } else if (action.type === 'postit_resize') {
                        // Actualizar tamaño del post-it inmediatamente
                        const history = userWhiteboards[targetMode].history;
                        const postItIndex = history.findIndex(a => a.id === action.originalId);
                        if (postItIndex !== -1) {
                            history[postItIndex].x = action.x;
                            history[postItIndex].y = action.y;
                            history[postItIndex].width = action.width;
                            history[postItIndex].height = action.height;
                            // Redibujar inmediatamente para ver el redimensionamiento en tiempo real
                            redrawFromHistory();
                        }
                        processedActions.add(actionKey);
                    } else if (action.type === 'clear') {
                        whiteboardCtx.clearRect(0, 0, whiteboardCanvas.width, whiteboardCanvas.height);
                        // Marcar como procesada SOLO después de aplicarla exitosamente
                        processedActions.add(actionKey);
                    }
                } else if (attempts < maxAttempts && (isWhiteboardOpen || panelStillOpen)) {
                    // Intentar de nuevo después de 50ms
                    setTimeout(tryApplyAction, 50);
                } else if (attempts >= maxAttempts) {
                    console.log('[Whiteboard] ⚠️ No se pudo aplicar acción después de', maxAttempts, 'intentos');
                }
            };
            
            // Intentar aplicar después de un breve delay
            setTimeout(tryApplyAction, 10);
        } else {
            console.log('[Whiteboard] ⚠️ Pizarra cerrada, acción guardada en historial');
        }
        
        // La acción ya está guardada en el historial, se aplicará cuando la pizarra se abra
        return;
    }
    
    // Si la acción es para otra pizarra, solo guardarla pero no dibujarla aquí
    if (targetMode !== currentWhiteboardMode) {
        // La acción es para otra pizarra, solo guardarla en el historial
        return;
    }
    
    // Verificar una vez más que el canvas esté listo antes de continuar
    // Usar verificación robusta del estado de la pizarra
    const whiteboardPanelCheck = document.getElementById('whiteboard-panel');
    const panelIsOpenCheck = whiteboardPanelCheck && whiteboardPanelCheck.classList.contains('open');
    const wbIsOpenCheck = isWhiteboardOpen || panelIsOpenCheck;
    
    if (!whiteboardCtx || !whiteboardCanvas) {
        // Intentar reinicializar si la pizarra está abierta (según DOM o variable)
        if (wbIsOpenCheck && canvasElement) {
            initializeWhiteboard();
            // Verificar de nuevo
            if (!whiteboardCtx || !whiteboardCanvas) {
                return; // No se pudo inicializar, la acción se guardó en historial
            }
        } else {
            return; // Pizarra cerrada, acción guardada en historial
        }
    }
    
    // Verificar dimensiones del canvas
    if (whiteboardCanvas.width === 0 || whiteboardCanvas.height === 0) {
        resizeCanvas();
        if (whiteboardCanvas.width === 0 || whiteboardCanvas.height === 0) {
            return; // Canvas sin dimensiones, acción guardada en historial
        }
    }
    
    // CRÍTICO: Para acciones de borrado (eraser o clear) de OTROS USUARIOS, redibujar desde historial
    // en lugar de aplicar directamente. Esto asegura que el borrado se aplique al estado
    // correcto del canvas, respetando el orden cronológico de todas las acciones.
    // IMPORTANTE: NO redibujar si es nuestra propia acción, porque ya la aplicamos localmente
    // y redibujar podría causar que se borren nuestros propios dibujos si hay un clear en el historial.
    const isEraserAction = action.tool === 'eraser' || action.type === 'clear';
    // currentUID ya está declarado arriba, reutilizar
    const isOurEraserAction = isEraserAction && action.userId && String(action.userId) === String(currentUID);
    const isOurEraserActionById = isEraserAction && action.id && (action.id === lastSentActionId || sentActionIds.has(action.id));
    
    if (isEraserAction && targetMode === currentWhiteboardMode && !isOurEraserAction && !isOurEraserActionById) {
        console.log('[Whiteboard] 🧹 Acción de borrado de OTRO USUARIO recibida - redibujando desde historial para garantizar orden cronológico:', {
            actionId: action.id,
            type: action.type,
            tool: action.tool,
            whiteboardMode: targetMode,
            fromUserId: action.userId,
            currentUID: currentUID,
            isOurAction: isOurEraserAction || isOurEraserActionById
        });
        
        // OPTIMIZACIÓN: Usar requestAnimationFrame para diferir el redibujado al siguiente frame
        // Esto mejora la respuesta visual y reduce la latencia percibida
        requestAnimationFrame(() => {
            // Redibujar desde historial para asegurar que todas las acciones se apliquen en orden cronológico
            // Esto garantiza que el borrado afecte al contenido correcto
            redrawFromHistory();
        });
        
        // Marcar como procesada inmediatamente (el redibujado se hará en el siguiente frame)
        processedActions.add(actionKey);
        return;
    } else if (isEraserAction && (isOurEraserAction || isOurEraserActionById)) {
        // Es nuestra propia acción de borrado, no redibujar (ya la aplicamos localmente)
        console.log('[Whiteboard] ⏭️ Acción de borrado PROPIA detectada - NO redibujando (ya aplicada localmente):', {
            actionId: action.id,
            type: action.type,
            tool: action.tool,
            userId: action.userId,
            currentUID: currentUID
        });
        
        // Marcar como procesada pero NO redibujar
        processedActions.add(actionKey);
        return;
    }
    
    // Mostrar indicador de que otro usuario está dibujando
    if (action.userName) {
        showDrawingIndicator(action.userName);
    }
    
    // Aplicar acción de movimiento de texto
    if (action.type === 'text_move') {
        // Evitar procesar nuestros propios movimientos en tiempo real (ya los vemos localmente)
        const currentUID = getCurrentUID();
        const isOurAction = action.userId && String(action.userId) === String(currentUID);
        
        // Solo ignorar si es nuestra acción Y estamos moviendo activamente
        // Si no estamos moviendo, procesar para sincronización
        if (isOurAction && isMovingText) {
            // Es nuestro propio movimiento en tiempo real, ya lo vemos localmente
            processedActions.add(actionKey);
            return;
        }
        
        // Buscar el texto original en el historial
        const history = userWhiteboards[targetMode].history;
        const textIndex = history.findIndex(a => a.id === action.originalId);
        
        if (textIndex !== -1) {
            // Actualizar posición del texto inmediatamente
            history[textIndex].x = action.x;
            history[textIndex].y = action.y;
            
            // Redibujar INMEDIATAMENTE si estamos en la pizarra correcta
            if (targetMode === currentWhiteboardMode && whiteboardCtx && whiteboardCanvas) {
                // Forzar redibujado inmediato para ver el movimiento en tiempo real
                redrawFromHistory();
            }
        } else {
            // Si no encontramos el texto, podría ser que aún no se haya cargado
            // Intentar buscar en todas las pizarras
            for (const mode in userWhiteboards) {
                const boardHistory = userWhiteboards[mode].history;
                const idx = boardHistory.findIndex(a => a.id === action.originalId);
                if (idx !== -1) {
                    boardHistory[idx].x = action.x;
                    boardHistory[idx].y = action.y;
                    if (mode === currentWhiteboardMode && whiteboardCtx && whiteboardCanvas) {
                        redrawFromHistory();
                    }
                    break;
                }
            }
        }
        
        processedActions.add(actionKey);
        return;
    }
    
    // Aplicar la acción en el canvas (optimizado para mejor rendimiento)
    if (action.type === 'draw') {
        // LOG ESPECÍFICO PARA BORRADO
        if (action.tool === 'eraser') {
            console.log('[Whiteboard] 🧹 APLICANDO BORRADO:', {
                actionId: action.id,
                actionKey: actionKey,
                fromX: action.fromX,
                fromY: action.fromY,
                toX: action.toX,
                toY: action.toY,
                lineWidth: action.lineWidth,
                userId: action.userId,
                userName: action.userName,
                whiteboardMode: action.whiteboardMode || targetMode,
                isOurAction: isOurAction,
                timestamp: new Date().toISOString()
            });
        }
        
        whiteboardCtx.beginPath();
        whiteboardCtx.moveTo(action.fromX, action.fromY);
        whiteboardCtx.lineTo(action.toX, action.toY);
        
        if (action.tool === 'pen') {
            whiteboardCtx.strokeStyle = action.color;
            whiteboardCtx.globalCompositeOperation = 'source-over';
            whiteboardCtx.lineWidth = action.lineWidth;
        } else if (action.tool === 'eraser') {
            whiteboardCtx.strokeStyle = '#ffffff';
            whiteboardCtx.globalCompositeOperation = 'destination-out';
            // CRÍTICO: Multiplicar por 2 para mantener consistencia con el borrado local
            // El borrador local usa lineWidth * 2, así que debemos hacer lo mismo aquí
            whiteboardCtx.lineWidth = action.lineWidth * 2;
        }
        whiteboardCtx.lineCap = 'round';
        whiteboardCtx.lineJoin = 'round';
        whiteboardCtx.stroke();
        
        if (action.tool === 'eraser') {
            whiteboardCtx.globalCompositeOperation = 'source-over';
            console.log('[Whiteboard] ✅ BORRADO APLICADO AL CANVAS:', {
                actionId: action.id,
                actionKey: actionKey
            });
        }
        
        // Marcar como procesada SOLO después de aplicarla exitosamente al canvas
        processedActions.add(actionKey);
        
        // NO guardar de nuevo en historial (ya está guardado arriba)
    } else if (action.type === 'shape') {
        whiteboardCtx.strokeStyle = action.color;
        whiteboardCtx.lineWidth = action.lineWidth;
        whiteboardCtx.globalCompositeOperation = 'source-over';
        
        if (action.tool === 'line') {
            whiteboardCtx.beginPath();
            whiteboardCtx.moveTo(action.fromX, action.fromY);
            whiteboardCtx.lineTo(action.toX, action.toY);
            whiteboardCtx.stroke();
        } else if (action.tool === 'rectangle') {
            whiteboardCtx.strokeRect(action.x, action.y, action.width, action.height);
        } else if (action.tool === 'circle') {
            whiteboardCtx.beginPath();
            whiteboardCtx.arc(action.centerX, action.centerY, action.radius, 0, 2 * Math.PI);
            whiteboardCtx.stroke();
        }
        processedActions.add(actionKey);
    } else if (action.type === 'text') {
        // IMPORTANTE: Verificar que no sea una acción de movimiento de texto mal procesada
        // Si tiene originalId, es probablemente un text_move mal procesado, no crear nueva acción
        if (action.originalId) {
            // Es una acción de movimiento, no debería estar aquí como 'text'
            console.warn('[Whiteboard] ⚠️ Acción de texto con originalId detectada (probablemente text_move mal procesado):', action);
            processedActions.add(actionKey);
            return;
        }
        
        whiteboardCtx.fillStyle = action.color;
        const fontSize = action.fontSize || 16;
        const fontFamily = action.fontFamily || 'Arial';
        whiteboardCtx.font = `${fontSize}px ${fontFamily}`;
        
        // Si hay ancho y alto, dibujar con word wrap
        if (action.width && action.height) {
            const lines = wrapText(action.text, action.width - 16, fontSize, fontFamily);
            const lineHeight = fontSize * 1.2;
            const startY = action.y + fontSize + 4;
            
            lines.forEach((line, index) => {
                const lineY = startY + (index * lineHeight);
                if (lineY <= action.y + action.height - 4) {
                    whiteboardCtx.fillText(line, action.x + 8, lineY);
                }
            });
        } else {
            whiteboardCtx.fillText(action.text, action.x, action.y);
        }
        processedActions.add(actionKey);
    } else if (action.type === 'postit_delete') {
        // Manejar borrado de post-it recibido por WebSocket
        const history = userWhiteboards[targetMode].history;
        const postItIndex = history.findIndex(a => a.id === action.originalId);
        if (postItIndex !== -1) {
            // Eliminar el post-it del historial
            history.splice(postItIndex, 1);
            console.log('[Whiteboard] 🗑️ Post-it eliminado (WebSocket):', {
                originalId: action.originalId,
                actionId: action.id,
                fromUser: action.userName || action.userId,
                remainingPostIts: history.filter(a => a.type === 'postit').length
            });
            
            // Redibujar si estamos en la pizarra correcta
            if (targetMode === currentWhiteboardMode && whiteboardCtx && whiteboardCanvas) {
                redrawFromHistory();
            }
        }
        processedActions.add(actionKey);
    } else if (action.type === 'clear') {
        whiteboardCtx.clearRect(0, 0, whiteboardCanvas.width, whiteboardCanvas.height);
        drawingHistory = [];
        historyIndex = -1;
        
        // Si es nuestra propia acción de limpiar, resetear lastSentActionId y sentActionIds
        if (action.id && (action.id === lastSentActionId || sentActionIds.has(action.id))) {
            lastSentActionId = null;
            sentActionIds.clear();
        }
        
        // Limpiar también el historial de la pizarra correspondiente
        if (userWhiteboards[targetMode]) {
            userWhiteboards[targetMode].history = [];
        }
        
        // Marcar como procesada SOLO después de aplicarla exitosamente al canvas
        processedActions.add(actionKey);
        
        // NO limpiar processedActions aquí - mantener el cache para evitar re-procesar acciones antiguas
        // processedActions solo se limpia cuando el usuario local limpia explícitamente
    }
}

// Conectar WebSocket para tiempo real
function connectWhiteboardWebSocket() {
    const CHAT_ROOM = sessionStorage.getItem('room');
    if (!CHAT_ROOM) {
        console.warn('[Whiteboard] No hay sala definida para WebSocket');
        return;
    }
    
    // Si ya está conectado, no hacer nada
    if (whiteboardSocket && whiteboardSocket.readyState === WebSocket.OPEN) {
        return;
    }
    
    // Determinar protocolo (ws o wss)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/whiteboard/${CHAT_ROOM}/`;
    
    try {
        whiteboardSocket = new WebSocket(wsUrl);
        
        whiteboardSocket.onopen = () => {
            websocketConnected = true;
            websocketReconnectAttempts = 0;
            console.log('[Whiteboard] ✅ WebSocket conectado - tiempo real activado');
        };
        
        whiteboardSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'whiteboard_action' && data.action) {
                    // CRÍTICO: Agregar created_at a la acción recibida si no lo tiene
                    // Esto es esencial para el ordenamiento cronológico correcto
                    // Si la acción ya tiene created_at, mantenerlo; si no, usar el timestamp actual
                    if (!data.action.created_at) {
                        data.action.created_at = Date.now();
                        data.action.created_at_iso = new Date().toISOString();
                        console.log('[Whiteboard] ⏰ Agregado created_at a acción recibida por WebSocket:', {
                            actionId: data.action.id,
                            created_at: data.action.created_at
                        });
                    }
                    
                    // LOG ESPECÍFICO PARA BORRADO RECIBIDO POR WEBSOCKET
                    if (data.action.tool === 'eraser' || data.action.type === 'clear') {
                        console.log('[Whiteboard] 📥 BORRADO RECIBIDO POR WEBSOCKET:', {
                            actionId: data.action.id,
                            type: data.action.type,
                            tool: data.action.tool,
                            userId: data.action.userId,
                            user_id: data.user_id,
                            username: data.username,
                            messageId: data.action.messageId,
                            created_at: data.action.created_at,
                            created_at_iso: data.action.created_at_iso
                        });
                    }
                    
                    // Aplicar acción recibida (evitar procesar nuestras propias acciones)
                    // Comparar usando userId de la acción (UID de Agora) o user_id del mensaje (ID de Django)
                    const actionUserId = data.action.userId || data.action.user_id || data.user_id;
                    const currentUID = getCurrentUID();
                    
                    // Para text_move, text_edit, postit_move y postit_resize, aplicar siempre (excepto si es nuestra propia acción en tiempo real)
                    // Para otras acciones, verificar que no sea nuestra propia acción
                    const isTextMove = data.action.type === 'text_move';
                    const isTextEdit = data.action.type === 'text_edit';
                    const isPostItMove = data.action.type === 'postit_move';
                    const isPostItResize = data.action.type === 'postit_resize';
                    const isEraserAction = data.action.tool === 'eraser' || data.action.type === 'clear';
                    const isOurAction = actionUserId && String(actionUserId) === String(currentUID);
                    
                    // LOG ESPECÍFICO para acciones de borrado
                    if (isEraserAction) {
                        console.log('[Whiteboard] 🔍 ANALIZANDO BORRADO RECIBIDO:', {
                            actionId: data.action.id,
                            actionUserId: actionUserId,
                            currentUID: currentUID,
                            isOurAction: isOurAction,
                            willProcess: !isOurAction
                        });
                    }
                    
                    if (isTextMove) {
                        // Para text_move, aplicar si no es nuestra acción O si no estamos moviendo activamente
                        // Esto permite que otros usuarios vean el movimiento en tiempo real
                        if (!isOurAction || !isMovingText) {
                            // Optimización: actualizar y dibujar directamente sin redibujar toda la pizarra
                            const targetMode = data.action.whiteboardMode || currentWhiteboardMode;
                            if (!userWhiteboards[targetMode]) {
                                initializeUserWhiteboard(targetMode);
                            }
                            
                            const history = userWhiteboards[targetMode].history;
                            const textIndex = history.findIndex(a => a.id === data.action.originalId);
                            
                            if (textIndex !== -1) {
                                // Actualizar posición en el historial (SOLO la posición, no crear nueva acción)
                                history[textIndex].x = data.action.x;
                                history[textIndex].y = data.action.y;
                                
                                // Redibujar solo el texto movido (más rápido que redibujar toda la pizarra)
                                redrawFromHistoryExcluding(data.action.originalId);
                                
                                // Dibujar el texto en la nueva posición con sus estilos originales (SOLO visual, no guardar)
                                const textAction = history[textIndex];
                                drawTextOnly(textAction.x, textAction.y, textAction.text, 
                                        textAction.width, textAction.height,
                                        textAction.color, textAction.fontSize, textAction.fontFamily);
                                
                                // CRÍTICO: Marcar como procesada para evitar que se procese de nuevo y se cree como nueva acción
                                const actionKey = data.action.messageId ? `msg_${data.action.messageId}` : `action_${data.action.id}`;
                                processedActions.add(actionKey);
                                
                                console.log('[Whiteboard] ⚡ Texto movido en tiempo real:', {
                                    id: data.action.originalId,
                                    x: data.action.x,
                                    y: data.action.y,
                                    actionKey: actionKey
                                });
                            } else {
                                // Si no existe, usar applyDrawingAction normal
                                applyDrawingAction(data.action);
                            }
                        }
                    } else if (isTextEdit) {
                        // Para text_edit, aplicar si no es nuestra acción
                        // Esto permite que otros usuarios vean la edición en tiempo real
                        if (!isOurAction) {
                            // Optimización: actualizar y dibujar directamente sin redibujar toda la pizarra
                            const targetMode = data.action.whiteboardMode || currentWhiteboardMode;
                            if (!userWhiteboards[targetMode]) {
                                initializeUserWhiteboard(targetMode);
                            }
                            
                            const history = userWhiteboards[targetMode].history;
                            const textIndex = history.findIndex(a => a.id === data.action.originalId);
                            
                            if (textIndex !== -1) {
                                // Actualizar el texto en el historial
                                history[textIndex].text = data.action.text;
                                
                                // Redibujar solo el texto editado (más rápido que redibujar toda la pizarra)
                                redrawFromHistoryExcluding(data.action.originalId);
                                
                                // Dibujar el texto con el nuevo contenido y sus estilos originales (SOLO visual, no guardar)
                                const textAction = history[textIndex];
                                drawTextOnly(textAction.x, textAction.y, textAction.text, 
                                        textAction.width, textAction.height,
                                        textAction.color, textAction.fontSize, textAction.fontFamily);
                                
                                console.log('[Whiteboard] ⚡ Texto editado en tiempo real:', {
                                    id: data.action.originalId,
                                    newText: data.action.text
                                });
                            } else {
                                // Si no existe, usar applyDrawingAction normal
                                applyDrawingAction(data.action);
                            }
                        }
                    } else if (isPostItMove) {
                        // Para postit_move, aplicar si no es nuestra acción O si no estamos moviendo activamente
                        // Esto permite que otros usuarios vean el movimiento en tiempo real
                        if (!isOurAction || !isMovingPostIt) {
                            // Optimización: actualizar y dibujar directamente sin redibujar toda la pizarra
                            const targetMode = data.action.whiteboardMode || currentWhiteboardMode;
                            if (!userWhiteboards[targetMode]) {
                                initializeUserWhiteboard(targetMode);
                            }
                            
                            const history = userWhiteboards[targetMode].history;
                            const postItIndex = history.findIndex(a => a.id === data.action.originalId);
                            
                            if (postItIndex !== -1) {
                                // Actualizar posición en el historial
                                history[postItIndex].x = data.action.x;
                                history[postItIndex].y = data.action.y;
                                
                                // Redibujar solo el post-it movido (más rápido que redibujar toda la pizarra)
                                // Primero limpiar el área anterior del post-it
                                const oldPostIt = history[postItIndex];
                                const oldX = oldPostIt.x || 0;
                                const oldY = oldPostIt.y || 0;
                                const oldWidth = oldPostIt.width || 200;
                                const oldHeight = oldPostIt.height || 150;
                                
                                // Redibujar desde el historial excluyendo este post-it
                                redrawFromHistoryExcluding(data.action.originalId);
                                
                                // Dibujar el post-it en la nueva posición
                                drawPostIt(history[postItIndex]);
                                
                                console.log('[Whiteboard] ⚡ Post-it movido en tiempo real:', {
                                    id: data.action.originalId,
                                    x: data.action.x,
                                    y: data.action.y
                                });
                            } else {
                                // Si no existe, usar applyDrawingAction normal
                                applyDrawingAction(data.action);
                            }
                        }
                    } else if (isPostItResize) {
                        // Para postit_resize, aplicar si no es nuestra acción O si no estamos redimensionando activamente
                        // Esto permite que otros usuarios vean el redimensionamiento en tiempo real
                        if (!isOurAction || !isResizingPostIt) {
                            // Optimización: actualizar y dibujar directamente sin redibujar toda la pizarra
                            const targetMode = data.action.whiteboardMode || currentWhiteboardMode;
                            if (!userWhiteboards[targetMode]) {
                                initializeUserWhiteboard(targetMode);
                            }
                            
                            const history = userWhiteboards[targetMode].history;
                            const postItIndex = history.findIndex(a => a.id === data.action.originalId);
                            
                            if (postItIndex !== -1) {
                                // Actualizar tamaño y posición en el historial
                                history[postItIndex].x = data.action.x;
                                history[postItIndex].y = data.action.y;
                                history[postItIndex].width = data.action.width;
                                history[postItIndex].height = data.action.height;
                                
                                // Redibujar solo el post-it redimensionado (más rápido que redibujar toda la pizarra)
                                // Primero limpiar el área anterior del post-it
                                const oldPostIt = history[postItIndex];
                                const oldX = oldPostIt.x || 0;
                                const oldY = oldPostIt.y || 0;
                                const oldWidth = oldPostIt.width || 200;
                                const oldHeight = oldPostIt.height || 150;
                                
                                // Redibujar desde el historial excluyendo este post-it
                                redrawFromHistoryExcluding(data.action.originalId);
                                
                                // Dibujar el post-it con el nuevo tamaño
                                drawPostIt(history[postItIndex]);
                                
                                console.log('[Whiteboard] ⚡ Post-it redimensionado en tiempo real:', {
                                    id: data.action.originalId,
                                    x: data.action.x,
                                    y: data.action.y,
                                    width: data.action.width,
                                    height: data.action.height
                                });
                            } else {
                                // Si no existe, usar applyDrawingAction normal
                                applyDrawingAction(data.action);
                            }
                        }
                        } else {
                            // Para otras acciones (incluyendo texto y post-it), aplicar solo si no es nuestra propia acción
                            // IMPORTANTE: Para texto y post-it, verificar que tenga id, pero también permitir si viene de otro usuario
                            const hasValidId = data.action.id && !sentActionIds.has(data.action.id);
                            const isFromOtherUser = actionUserId && String(actionUserId) !== String(currentUID);
                            
                            // LOG ESPECÍFICO para acciones de borrado antes de procesar
                            if (isEraserAction) {
                                console.log('[Whiteboard] 🔍 DECISIÓN DE PROCESAMIENTO DE BORRADO:', {
                                    actionId: data.action.id,
                                    isOurAction: isOurAction,
                                    isFromOtherUser: isFromOtherUser,
                                    hasValidId: hasValidId,
                                    willApply: !isOurAction
                                });
                            }
                            
                            // Para acciones de borrado, SIEMPRE aplicar si viene de otro usuario
                            // Esto es crítico para la sincronización
                            if (isEraserAction && isFromOtherUser) {
                                console.log('[Whiteboard] ✅ APLICANDO BORRADO DE OTRO USUARIO:', {
                                    actionId: data.action.id,
                                    fromUser: actionUserId,
                                    currentUID: currentUID
                                });
                                applyDrawingAction(data.action);
                            } else if (isEraserAction && isOurAction) {
                                console.log('[Whiteboard] ⏭️ OMITIENDO BORRADO PROPIO (ya aplicado localmente):', {
                                    actionId: data.action.id
                                });
                            }
                            
                            // Para post-its, siempre aplicar si viene de otro usuario (sincronización en tiempo real)
                            const isPostIt = data.action.type === 'postit';
                            if (isPostIt && isFromOtherUser) {
                            console.log('[Whiteboard] 📥 Post-it recibido por WebSocket:', {
                                id: data.action.id,
                                text: data.action.text ? data.action.text.substring(0, 20) + '...' : 'sin texto',
                                fromUser: actionUserId,
                                currentUID: currentUID,
                                mode: data.action.whiteboardMode || currentWhiteboardMode,
                                backgroundColor: data.action.backgroundColor || 'no especificado'
                            });
                            
                            // Aplicar inmediatamente para sincronización en tiempo real
                            // Asegurarse de que el post-it esté en el historial correcto
                            const targetMode = data.action.whiteboardMode || currentWhiteboardMode;
                            if (!userWhiteboards[targetMode]) {
                                initializeUserWhiteboard(targetMode);
                            }
                            
                            const history = userWhiteboards[targetMode].history;
                            const existsInHistory = history.some(a => {
                                if (a.id === data.action.id) return true;
                                if (data.action.messageId && a.messageId === data.action.messageId) return true;
                                return false;
                            });
                            
                            if (!existsInHistory) {
                                // Guardar en el historial antes de dibujar
                                history.push(data.action);
                                console.log('[Whiteboard] 💾 Post-it guardado en historial antes de dibujar');
                            }
                            
                            // Dibujar inmediatamente (sin esperar a applyDrawingAction)
                            // Asegurar que el color esté presente
                            if (!data.action.backgroundColor) {
                                console.warn('[Whiteboard] ⚠️ Post-it recibido sin backgroundColor, usando color por defecto');
                                data.action.backgroundColor = currentPostItColor;
                            }
                            drawPostIt(data.action);
                            
                            console.log('[Whiteboard] ✅ Post-it dibujado inmediatamente con color:', data.action.backgroundColor);
                            return; // Salir temprano para evitar procesamiento adicional
                        }
                        
                        // Aplicar si:
                        // 1. Es de otro usuario Y tiene un ID válido (no lo hemos enviado nosotros)
                        // 2. O si es texto/post-it/borrado y es de otro usuario (siempre debe sincronizarse)
                        // IMPORTANTE: Las acciones de borrado deben aplicarse SIEMPRE si vienen de otro usuario
                        const shouldApply = isFromOtherUser && (
                            hasValidId || 
                            data.action.type === 'text' || 
                            data.action.type === 'postit' ||
                            isEraserAction  // CRÍTICO: Aplicar borrados de otros usuarios siempre
                        );
                        
                        if (shouldApply) {
                            // Log temporal para debugging de texto
                            if (data.action.type === 'text') {
                                console.log('[Whiteboard] 📝 Procesando texto recibido por WebSocket:', {
                                    text: data.action.text,
                                    fromUser: actionUserId,
                                    currentUser: currentUID,
                                    hasId: !!data.action.id,
                                    idInSent: data.action.id ? sentActionIds.has(data.action.id) : false
                                });
                            }
                            applyDrawingAction(data.action);
                        } else if (data.action.type === 'text') {
                            // Log cuando el texto NO se procesa
                            console.warn('[Whiteboard] ⚠️ Texto NO procesado:', {
                                text: data.action.text,
                                actionUserId: actionUserId,
                                currentUID: currentUID,
                                isFromOtherUser: isFromOtherUser,
                                hasValidId: hasValidId,
                                hasId: !!data.action.id
                            });
                        } else if (isEraserAction && !isFromOtherUser) {
                            // Log cuando el borrado NO se procesa porque es nuestro
                            console.log('[Whiteboard] ⏭️ Borrado NO procesado (es nuestra propia acción):', {
                                actionId: data.action.id,
                                actionUserId: actionUserId,
                                currentUID: currentUID
                            });
                        }
                    }
                }
            } catch (e) {
                console.error('[Whiteboard] Error parseando mensaje WebSocket:', e);
            }
        };
        
        whiteboardSocket.onerror = (error) => {
            console.error('[Whiteboard] Error en WebSocket:', error);
        };
        
        whiteboardSocket.onclose = () => {
            websocketConnected = false;
            console.log('[Whiteboard] ⚠️ WebSocket desconectado');
            
            // Intentar reconectar si no excedimos el límite
            if (websocketReconnectAttempts < MAX_RECONNECT_ATTEMPTS && isWhiteboardOpen) {
                websocketReconnectAttempts++;
                setTimeout(() => {
                    console.log(`[Whiteboard] 🔄 Intentando reconectar WebSocket (${websocketReconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
                    connectWhiteboardWebSocket();
                }, 2000 * websocketReconnectAttempts); // Backoff exponencial
            }
        };
    } catch (e) {
        console.error('[Whiteboard] Error creando WebSocket:', e);
        websocketConnected = false;
    }
}

// Desconectar WebSocket
function disconnectWhiteboardWebSocket() {
    if (whiteboardSocket) {
        whiteboardSocket.close();
        whiteboardSocket = null;
        websocketConnected = false;
        console.log('[Whiteboard] WebSocket desconectado');
    }
}

// Enviar acción de dibujo a otros participantes (usa WebSocket si está disponible, sino HTTP)
function sendDrawingAction(action) {
    const CHAT_ROOM = sessionStorage.getItem('room');
    if (!CHAT_ROOM) {
        console.warn('[Whiteboard] No hay sala definida');
        return;
    }
    
    // PRIORIDAD: Usar WebSocket si está conectado (tiempo real sin lag)
    if (websocketConnected && whiteboardSocket && whiteboardSocket.readyState === WebSocket.OPEN) {
        try {
            // CRÍTICO: Agregar created_at a la acción si no lo tiene
            // Esto es esencial para el ordenamiento cronológico correcto
            if (!action.created_at) {
                action.created_at = Date.now();
                action.created_at_iso = new Date().toISOString();
            }
            
            // LOG ESPECÍFICO PARA BORRADO AL ENVIAR
            if (action.tool === 'eraser' || action.type === 'clear') {
                console.log('[Whiteboard] 📤 ENVIANDO BORRADO POR WEBSOCKET:', {
                    actionId: action.id,
                    type: action.type,
                    tool: action.tool,
                    fromX: action.fromX,
                    fromY: action.fromY,
                    toX: action.toX,
                    toY: action.toY,
                    lineWidth: action.lineWidth,
                    userId: action.userId,
                    room: CHAT_ROOM,
                    created_at: action.created_at,
                    created_at_iso: action.created_at_iso
                });
            }
            
            const message = {
                type: 'whiteboard_action',
                action: action,
                room_name: CHAT_ROOM
            };
            whiteboardSocket.send(JSON.stringify(message));
            
            // Log para debugging de post-its
            if (action.type === 'postit') {
                console.log('[Whiteboard] ✅ Post-it enviado por WebSocket:', {
                    id: action.id,
                    text: action.text ? action.text.substring(0, 20) + '...' : 'sin texto',
                    room: CHAT_ROOM
                });
            }
            
            // LOG DE CONFIRMACIÓN PARA BORRADO
            if (action.tool === 'eraser' || action.type === 'clear') {
                console.log('[Whiteboard] ✅ BORRADO ENVIADO EXITOSAMENTE POR WEBSOCKET:', {
                    actionId: action.id
                });
            }
            
            return; // Salir aquí, ya se envió por WebSocket
        } catch (e) {
            console.error('[Whiteboard] Error enviando por WebSocket, fallback a HTTP:', e);
            // Continuar con HTTP como fallback
        }
    } else {
        // Log si WebSocket no está disponible
        if (action.type === 'postit') {
            console.warn('[Whiteboard] ⚠️ WebSocket no disponible para post-it, usando HTTP fallback:', {
                websocketConnected: websocketConnected,
                socketExists: !!whiteboardSocket,
                socketState: whiteboardSocket ? whiteboardSocket.readyState : 'no socket'
            });
        }
    }
    
    // FALLBACK: Usar HTTP si WebSocket no está disponible
    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        console.warn('[Whiteboard] No se pudo obtener token CSRF');
        return;
    }
    
    const message = `WHITEBOARD:${JSON.stringify(action)}`;
    
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
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            console.error('[Whiteboard] ❌ Error en respuesta del servidor:', data.error);
        }
    })
    .catch(error => {
        console.error('[Whiteboard] Error enviando acción de pizarra:', error);
    });
}

// Cambiar herramienta
function setTool(tool) {
    const previousTool = currentTool;
    
    // Si cambiamos de herramienta, ocultar botón de eliminar si estaba visible
    if (previousTool !== tool && postItDeleteButton) {
        hidePostItDeleteButton();
        selectedPostItAction = null;
    }
    
    currentTool = tool;
    
    // LOG ESPECÍFICO PARA BORRADOR
    if (tool === 'eraser') {
        console.log('[Whiteboard] 🧹 BORRADOR SELECCIONADO:', {
            previousTool: previousTool,
            newTool: tool,
            timestamp: new Date().toISOString()
        });
    }
    
    // Actualizar UI
    document.querySelectorAll('.whiteboard-tool-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const toolBtn = document.querySelector(`[data-tool="${tool}"]`);
    if (toolBtn) {
        toolBtn.classList.add('active');
        if (tool === 'eraser') {
            console.log('[Whiteboard] ✅ Botón de borrador activado en UI');
        }
    } else {
        if (tool === 'eraser') {
            console.warn('[Whiteboard] ⚠️ Botón de borrador no encontrado en UI');
        }
    }
    
    // Mostrar/ocultar controles de texto
    const textGroup = document.getElementById('whiteboard-text-group');
    if (textGroup) {
        if (tool === 'text' || tool === 'postit') {
            textGroup.style.display = 'flex';
            textGroup.style.alignItems = 'center';
            textGroup.style.gap = '8px';
            textGroup.style.opacity = '1';
            textGroup.style.pointerEvents = 'auto';
            console.log('[Whiteboard] ✅ Controles de texto mostrados');
        } else {
            textGroup.style.opacity = '0.5';
            textGroup.style.pointerEvents = 'none';
        }
    } else {
        console.warn('[Whiteboard] ⚠️ Grupo de controles de texto no encontrado');
    }
    
    // Mostrar/ocultar selector de color de post-it
    const postItColorGroup = document.getElementById('whiteboard-postit-color-group');
    if (postItColorGroup) {
        if (tool === 'postit') {
            postItColorGroup.style.display = 'flex';
            postItColorGroup.style.opacity = '1';
            postItColorGroup.style.pointerEvents = 'auto';
        } else {
            postItColorGroup.style.opacity = '0.5';
            postItColorGroup.style.pointerEvents = 'none';
        }
    }
    
    // Actualizar cursor según la herramienta
    if (whiteboardCanvas) {
        if (tool === 'pen') {
            whiteboardCanvas.style.cursor = 'crosshair';
        } else if (tool === 'eraser') {
            whiteboardCanvas.style.cursor = 'grab';
        } else if (tool === 'line' || tool === 'rectangle' || tool === 'circle') {
            whiteboardCanvas.style.cursor = 'crosshair';
        } else if (tool === 'text') {
            whiteboardCanvas.style.cursor = 'text';
        } else if (tool === 'postit') {
            whiteboardCanvas.style.cursor = 'crosshair';
        } else if (tool === 'move') {
            whiteboardCanvas.style.cursor = 'move';
        } else {
            whiteboardCanvas.style.cursor = 'default';
        }
    }
}

// Cambiar color
function setColor(color) {
    currentColor = color;
    
    // Actualizar UI
    document.querySelectorAll('.whiteboard-color-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const colorBtn = document.querySelector(`[data-color="${color}"]`);
    if (colorBtn) {
        colorBtn.classList.add('active');
    }
    
    // Actualizar input de color personalizado
    const customColorInput = document.getElementById('whiteboard-custom-color');
    if (customColorInput) {
        customColorInput.value = color;
    }
}

// Cambiar color de fondo del post-it
function setPostItColor(color) {
    if (!color) {
        console.warn('[Whiteboard] ⚠️ setPostItColor llamado sin color');
        return;
    }
    
    currentPostItColor = color;
    console.log('[Whiteboard] 🎨 Color de post-it cambiado a:', color);
    
    // Actualizar UI
    document.querySelectorAll('.whiteboard-postit-color-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const colorBtn = document.querySelector(`[data-postit-color="${color}"]`);
    if (colorBtn) {
        colorBtn.classList.add('active');
    }
    
    // Actualizar input de color personalizado de post-it
    const customPostItColorInput = document.getElementById('whiteboard-custom-postit-color');
    if (customPostItColorInput) {
        customPostItColorInput.value = color;
    }
}

// Establecer tamaño de fuente
function setFontSize(size) {
    currentFontSize = parseInt(size) || 16;
    
    // Actualizar UI
    const fontSizeInput = document.getElementById('whiteboard-font-size');
    if (fontSizeInput && fontSizeInput.value !== String(currentFontSize)) {
        fontSizeInput.value = currentFontSize;
    }
    
    const fontSizeDisplay = document.getElementById('whiteboard-font-size-display');
    if (fontSizeDisplay) {
        fontSizeDisplay.textContent = currentFontSize + 'px';
    }
}

// Establecer tipo de fuente
function setFontFamily(family) {
    currentFontFamily = family || 'Arial';
    
    // Actualizar UI
    const fontFamilySelect = document.getElementById('whiteboard-font-family');
    if (fontFamilySelect) {
        fontFamilySelect.value = currentFontFamily;
    }
}

// Cambiar grosor de línea
function setLineWidth(width) {
    currentLineWidth = width;
    
    // Actualizar UI
    document.querySelectorAll('.whiteboard-width-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const widthBtn = document.querySelector(`[data-width="${width}"]`);
    if (widthBtn) {
        widthBtn.classList.add('active');
    }
}

// Previsualizar forma mientras se arrastra
function previewShape(x1, y1, x2, y2) {
    if (!whiteboardCtx) return;
    
    whiteboardCtx.strokeStyle = currentColor;
    whiteboardCtx.lineWidth = currentLineWidth;
    whiteboardCtx.globalCompositeOperation = 'source-over';
    
    if (currentTool === 'line') {
        whiteboardCtx.beginPath();
        whiteboardCtx.moveTo(x1, y1);
        whiteboardCtx.lineTo(x2, y2);
        whiteboardCtx.stroke();
    } else if (currentTool === 'rectangle') {
        const width = x2 - x1;
        const height = y2 - y1;
        whiteboardCtx.strokeRect(x1, y1, width, height);
    } else if (currentTool === 'circle') {
        const radius = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
        whiteboardCtx.beginPath();
        whiteboardCtx.arc(x1, y1, radius, 0, 2 * Math.PI);
        whiteboardCtx.stroke();
    }
}

// Previsualizar rectángulo de texto durante el arrastre
function previewTextRect(x1, y1, x2, y2) {
    if (!whiteboardCtx) return;
    
    const x = Math.min(x1, x2);
    const y = Math.min(y1, y2);
    const width = Math.abs(x2 - x1);
    const height = Math.abs(y2 - y1);
    
    whiteboardCtx.strokeStyle = currentColor;
    whiteboardCtx.lineWidth = 2;
    whiteboardCtx.setLineDash([5, 5]); // Línea punteada para indicar que es temporal
    whiteboardCtx.globalCompositeOperation = 'source-over';
    whiteboardCtx.strokeRect(x, y, width, height);
    whiteboardCtx.setLineDash([]); // Restaurar línea sólida
}

// Dibujar forma final y guardarla
function drawShape(x1, y1, x2, y2) {
    if (!whiteboardCtx) return;
    
    whiteboardCtx.strokeStyle = currentColor;
    whiteboardCtx.lineWidth = currentLineWidth;
    whiteboardCtx.globalCompositeOperation = 'source-over';
    
    const actionId = `action_${Date.now()}_${++actionCounter}`;
    const currentUID = getCurrentUID();
    const currentUserName = getCurrentUser();
    const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
    
    let action = {
        id: actionId,
        type: 'shape',
        tool: currentTool,
        color: currentColor,
        lineWidth: currentLineWidth,
        userId: currentUID,
        userName: currentUserName,
        whiteboardMode: currentWhiteboardMode,
        created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico
        created_at_iso: new Date().toISOString()
    };
    
    if (currentTool === 'line') {
        whiteboardCtx.beginPath();
        whiteboardCtx.moveTo(x1, y1);
        whiteboardCtx.lineTo(x2, y2);
        whiteboardCtx.stroke();
        action.fromX = x1;
        action.fromY = y1;
        action.toX = x2;
        action.toY = y2;
    } else if (currentTool === 'rectangle') {
        const width = x2 - x1;
        const height = y2 - y1;
        whiteboardCtx.strokeRect(x1, y1, width, height);
        action.x = x1;
        action.y = y1;
        action.width = width;
        action.height = height;
    } else if (currentTool === 'circle') {
        const radius = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
        whiteboardCtx.beginPath();
        whiteboardCtx.arc(x1, y1, radius, 0, 2 * Math.PI);
        whiteboardCtx.stroke();
        action.centerX = x1;
        action.centerY = y1;
        action.radius = radius;
    }
    
    // Guardar en historial
    saveToHistory(action);
    
    // Guardar ID y enviar
    lastSentActionId = actionId;
    sentActionIds.add(actionId);
    
    if (sentActionIds.size > 1000) {
        sentActionIds.clear();
        if (lastSentActionId) {
            sentActionIds.add(lastSentActionId);
        }
    }
    
    isCurrentlyDrawing = true;
    showDrawingIndicator(currentUserName);
    sendDrawingAction(action);
}

// Agregar texto en una posición con tamaño específico
function addTextAtPosition(x, y, width, height) {
    if (!whiteboardCanvas) {
        console.warn('[Whiteboard] Canvas no disponible para texto');
        return;
    }
    
    const canvasContainer = whiteboardCanvas.parentElement;
    if (!canvasContainer) {
        console.warn('[Whiteboard] Contenedor del canvas no encontrado');
        return;
    }
    
    // Asegurar que el contenedor tenga position relative
    if (getComputedStyle(canvasContainer).position === 'static') {
        canvasContainer.style.position = 'relative';
    }
    
    // Obtener posición relativa al contenedor usando getBoundingClientRect
    const canvasRect = whiteboardCanvas.getBoundingClientRect();
    const containerRect = canvasContainer.getBoundingClientRect();
    
    // Calcular posición relativa al contenedor
    const relativeX = (canvasRect.left - containerRect.left) + x;
    const relativeY = (canvasRect.top - containerRect.top) + y;
    
    // Asegurar un tamaño mínimo
    const minWidth = 100;
    const minHeight = 30;
    const finalWidth = Math.max(width || minWidth, minWidth);
    const finalHeight = Math.max(height || minHeight, minHeight);
    
    // Crear textarea para permitir múltiples líneas
    const textInput = document.createElement('textarea');
    textInput.placeholder = 'Escribe aquí...';
    textInput.value = '';
    textInput.style.cssText = `
        position: absolute;
        left: ${relativeX}px;
        top: ${relativeY}px;
        width: ${finalWidth}px;
        height: ${finalHeight}px;
        border: 2px solid ${currentColor};
        padding: 4px 8px;
        font-size: ${Math.max(8, currentFontSize)}px;
        color: ${currentColor};
        background: rgba(255, 255, 255, 0.95);
        outline: none;
        z-index: 10000;
        font-family: ${currentFontFamily}, sans-serif;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        resize: none;
        overflow: auto;
    `;
    
    // Agregar al contenedor
    canvasContainer.appendChild(textInput);
    
    // Enfocar el textarea
    textInput.focus();
    
    // Función para finalizar el texto
    const finishText = () => {
        const text = textInput.value.trim();
        if (text) {
            // Dibujar el texto en el canvas
            drawText(x, y, text, finalWidth, finalHeight);
        }
        // Remover el textarea
        if (textInput.parentElement) {
            textInput.parentElement.removeChild(textInput);
        }
    };
    
    // Event listeners
    textInput.addEventListener('blur', finishText);
    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            // Ctrl+Enter o Cmd+Enter para finalizar
            e.preventDefault();
            finishText();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            if (textInput.parentElement) {
                textInput.parentElement.removeChild(textInput);
            }
        }
    });
    
    // Prevenir que el clic en el textarea cierre la pizarra o cause otros efectos
    textInput.addEventListener('mousedown', (e) => {
        e.stopPropagation();
    });
    textInput.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

// Manejar doble clic para editar texto
function handleDoubleClick(e) {
    if (!whiteboardCanvas || !whiteboardCtx) return;
    if (!canEditCurrentWhiteboard()) return;
    
    const rect = whiteboardCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Buscar texto en esa posición
    const textAction = getTextAtPosition(x, y);
    if (textAction) {
        e.preventDefault();
        e.stopPropagation();
        // Editar el texto existente
        editTextAtPosition(textAction);
    }
}

// Editar texto existente
function editTextAtPosition(textAction) {
    if (!whiteboardCanvas || !textAction) return;
    
    const canvasContainer = whiteboardCanvas.parentElement;
    if (!canvasContainer) return;
    
    // Asegurar que el contenedor tenga position relative
    if (getComputedStyle(canvasContainer).position === 'static') {
        canvasContainer.style.position = 'relative';
    }
    
    // Obtener posición relativa al contenedor
    const canvasRect = whiteboardCanvas.getBoundingClientRect();
    const containerRect = canvasContainer.getBoundingClientRect();
    
    // Calcular posición relativa al contenedor
    const relativeX = (canvasRect.left - containerRect.left) + textAction.x;
    const relativeY = (canvasRect.top - containerRect.top) + textAction.y;
    
    // Usar dimensiones del texto existente o valores por defecto
    const textWidth = textAction.width || 200;
    const textHeight = textAction.height || 30;
    
    // Crear textarea para editar el texto
    const textInput = document.createElement('textarea');
    textInput.value = textAction.text || '';
    textInput.style.cssText = `
        position: absolute;
        left: ${relativeX}px;
        top: ${relativeY}px;
        width: ${textWidth}px;
        height: ${textHeight}px;
        border: 2px solid ${textAction.color || currentColor};
        padding: 4px 8px;
        font-size: ${textAction.fontSize || currentFontSize}px;
        color: ${textAction.color || currentColor};
        background: rgba(255, 255, 255, 0.95);
        outline: none;
        z-index: 10000;
        font-family: ${textAction.fontFamily || currentFontFamily}, sans-serif;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        resize: none;
        overflow: auto;
    `;
    
    // Agregar al contenedor
    canvasContainer.appendChild(textInput);
    
    // Enfocar y seleccionar todo el texto
    textInput.focus();
    textInput.select();
    
    // Función para finalizar la edición
    const finishEdit = () => {
        const newText = textInput.value.trim();
        
        // Remover el textarea
        if (textInput.parentElement) {
            textInput.parentElement.removeChild(textInput);
        }
        
        // Si el texto cambió, actualizar
        if (newText !== (textAction.text || '')) {
            // Actualizar el texto en el historial
            const history = userWhiteboards[currentWhiteboardMode].history;
            const actionIndex = history.findIndex(a => a.id === textAction.id);
            
            if (actionIndex !== -1) {
                // Actualizar el texto
                history[actionIndex].text = newText;
                
                // Redibujar desde el historial
                redrawFromHistory();
                
                // Enviar acción de edición a otros usuarios
                const actionId = `edit_${Date.now()}_${++actionCounter}`;
                const currentUID = getCurrentUID();
                const currentUserName = getCurrentUser();
                const actionTimestamp = Date.now();
                
                const editAction = {
                    id: actionId,
                    type: 'text_edit',
                    originalId: textAction.id,
                    text: newText,
                    x: textAction.x,
                    y: textAction.y,
                    width: textAction.width,
                    height: textAction.height,
                    color: textAction.color,
                    fontSize: textAction.fontSize,
                    fontFamily: textAction.fontFamily,
                    userId: currentUID,
                    userName: currentUserName,
                    whiteboardMode: currentWhiteboardMode,
                    created_at: actionTimestamp,
                    created_at_iso: new Date().toISOString()
                };
                
                lastSentActionId = actionId;
                sentActionIds.add(actionId);
                sendDrawingAction(editAction);
                
                console.log('[Whiteboard] ✏️ Texto editado:', {
                    id: textAction.id,
                    oldText: textAction.text,
                    newText: newText
                });
            }
        }
    };
    
    // Event listeners
    textInput.addEventListener('blur', finishEdit);
    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            // Ctrl+Enter o Cmd+Enter para finalizar
            e.preventDefault();
            finishEdit();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            if (textInput.parentElement) {
                textInput.parentElement.removeChild(textInput);
            }
        }
    });
    
    // Prevenir que el clic en el textarea cause otros efectos
    textInput.addEventListener('mousedown', (e) => {
        e.stopPropagation();
    });
    textInput.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

// Dibujar texto solo visualmente (sin guardar en historial)
function drawTextOnly(x, y, text, width, height, color, fontSize, fontFamily) {
    if (!whiteboardCtx) return;
    
    // Usar parámetros proporcionados o valores actuales
    whiteboardCtx.fillStyle = color || currentColor;
    const textSize = fontSize || Math.max(8, currentFontSize);
    const textFamily = fontFamily || currentFontFamily;
    whiteboardCtx.font = `${textSize}px ${textFamily}`;
    
    // Si hay ancho y alto, dibujar el texto con word wrap
    if (width && height) {
        const lines = wrapText(text, width - 16, textSize, textFamily); // -16 para padding
        const lineHeight = textSize * 1.2;
        const startY = y + textSize + 4; // +4 para padding superior
        
        lines.forEach((line, index) => {
            const lineY = startY + (index * lineHeight);
            if (lineY <= y + height - 4) { // -4 para padding inferior
                whiteboardCtx.fillText(line, x + 8, lineY); // +8 para padding izquierdo
            }
        });
    } else {
        // Comportamiento original: una sola línea
        whiteboardCtx.fillText(text, x, y);
    }
}

// Dibujar texto final y guardarlo en historial
function drawText(x, y, text, width, height, color, fontSize, fontFamily) {
    if (!whiteboardCtx) return;
    
    // Dibujar visualmente
    drawTextOnly(x, y, text, width, height, color, fontSize, fontFamily);
    
    // Guardar en historial solo si es una nueva acción (no un movimiento)
    const actionId = `action_${Date.now()}_${++actionCounter}`;
    const currentUID = getCurrentUID();
    const currentUserName = getCurrentUser();
    const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
    
    const action = {
        id: actionId,
        type: 'text',
        x: x,
        y: y,
        text: text,
        width: width || null,
        height: height || null,
        color: color || currentColor,
        fontSize: fontSize || Math.max(8, currentFontSize),
        fontFamily: fontFamily || currentFontFamily,
        userId: currentUID,
        userName: currentUserName,
        whiteboardMode: currentWhiteboardMode,
        created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico
        created_at_iso: new Date().toISOString()
    };
    
    saveToHistory(action);
    lastSentActionId = actionId;
    sentActionIds.add(actionId);
    
    if (sentActionIds.size > 1000) {
        sentActionIds.clear();
        if (lastSentActionId) {
            sentActionIds.add(lastSentActionId);
        }
    }
    
    isCurrentlyDrawing = true;
    showDrawingIndicator(currentUserName);
    sendDrawingAction(action);
}

// Función auxiliar para dividir texto en líneas según el ancho
function wrapText(text, maxWidth, fontSize, fontFamily = 'Arial') {
    const words = text.split(' ');
    const lines = [];
    let currentLine = words[0];
    
    whiteboardCtx.font = `${fontSize}px ${fontFamily}`;
    
    for (let i = 1; i < words.length; i++) {
        const word = words[i];
        const testLine = currentLine + ' ' + word;
        const metrics = whiteboardCtx.measureText(testLine);
        const testWidth = metrics.width;
        
        if (testWidth > maxWidth && currentLine.length > 0) {
            lines.push(currentLine);
            currentLine = word;
        } else {
            currentLine = testLine;
        }
    }
    lines.push(currentLine);
    
    return lines;
}

// Previsualizar post-it durante el arrastre
function previewPostIt(x1, y1, x2, y2) {
    if (!whiteboardCtx) return;
    
    const x = Math.min(x1, x2);
    const y = Math.min(y1, y2);
    const width = Math.abs(x2 - x1);
    const height = Math.abs(y2 - y1);
    
    // Dibujar fondo con color del post-it
    whiteboardCtx.fillStyle = currentPostItColor;
    whiteboardCtx.globalCompositeOperation = 'source-over';
    whiteboardCtx.fillRect(x, y, width, height);
    
    // Dibujar borde punteado
    whiteboardCtx.strokeStyle = currentColor;
    whiteboardCtx.lineWidth = 2;
    whiteboardCtx.setLineDash([5, 5]);
    whiteboardCtx.strokeRect(x, y, width, height);
    whiteboardCtx.setLineDash([]);
}

// Agregar post-it en una posición con tamaño específico
function addPostItAtPosition(x, y, width, height) {
    if (!whiteboardCanvas) {
        console.warn('[Whiteboard] Canvas no disponible para post-it');
        return;
    }
    
    const canvasContainer = whiteboardCanvas.parentElement;
    if (!canvasContainer) {
        console.warn('[Whiteboard] Contenedor del canvas no encontrado');
        return;
    }
    
    // Asegurar que el contenedor tenga position relative
    if (getComputedStyle(canvasContainer).position === 'static') {
        canvasContainer.style.position = 'relative';
    }
    
    // Obtener posición relativa al contenedor
    const canvasRect = whiteboardCanvas.getBoundingClientRect();
    const containerRect = canvasContainer.getBoundingClientRect();
    
    const relativeX = (canvasRect.left - containerRect.left) + x;
    const relativeY = (canvasRect.top - containerRect.top) + y;
    
    // Asegurar un tamaño mínimo
    const minWidth = 150;
    const minHeight = 100;
    const finalWidth = Math.max(width || minWidth, minWidth);
    const finalHeight = Math.max(height || minHeight, minHeight);
    
    // Crear textarea para permitir múltiples líneas
    const textInput = document.createElement('textarea');
    textInput.placeholder = 'Escribe tu nota...';
    textInput.value = '';
    textInput.style.cssText = `
        position: absolute;
        left: ${relativeX}px;
        top: ${relativeY}px;
        width: ${finalWidth}px;
        height: ${finalHeight}px;
        border: 2px solid ${currentColor};
        padding: 8px;
        font-size: ${Math.max(12, currentFontSize)}px;
        color: ${currentColor};
        background: ${currentPostItColor || '#FFEB3B'};
        outline: none;
        z-index: 10000;
        font-family: ${currentFontFamily}, sans-serif;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        resize: none;
        overflow: auto;
    `;
    
    // Agregar al contenedor
    canvasContainer.appendChild(textInput);
    
    // Enfocar el textarea
    textInput.focus();
    
    // Función para finalizar el post-it
    const finishPostIt = () => {
        const text = textInput.value.trim();
        if (text) {
            // Remover el textarea primero
            if (textInput.parentElement) {
                textInput.parentElement.removeChild(textInput);
            }
            
            // Dibujar el post-it en el canvas (esto lo guardará en el historial y lo enviará)
            // NO redibujar antes porque drawPostIt ya dibuja el post-it directamente
            // Log para verificar el color antes de dibujar
            console.log('[Whiteboard] 🎨 Creando post-it con color:', {
                currentPostItColor: currentPostItColor,
                x, y, text: text.substring(0, 20) + '...'
            });
            drawPostIt(null, x, y, text, finalWidth, finalHeight);
        } else {
            // Si no hay texto, solo remover el textarea
            if (textInput.parentElement) {
                textInput.parentElement.removeChild(textInput);
            }
        }
    };
    
    // Event listeners
    textInput.addEventListener('blur', finishPostIt);
    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            finishPostIt();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            if (textInput.parentElement) {
                textInput.parentElement.removeChild(textInput);
            }
        }
    });
    
    // Prevenir que el clic en el textarea cause otros efectos
    textInput.addEventListener('mousedown', (e) => {
        e.stopPropagation();
    });
    textInput.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

// Dibujar post-it final
function drawPostIt(action, x, y, text, width, height) {
    if (!whiteboardCtx) return;
    
    // Si se pasa una acción, usar sus propiedades
    // IMPORTANTE: NO sobrescribir currentPostItColor cuando se redibuja desde historial
    // Solo usar el color de la acción para dibujar, pero mantener el color seleccionado actual
    if (action) {
        x = action.x;
        y = action.y;
        text = action.text || '';
        width = action.width || 200; // Valores por defecto si no existen
        height = action.height || 150;
        // NO actualizar currentPostItColor aquí - solo usar el color de la acción para dibujar
        // currentPostItColor debe mantenerse como el color seleccionado por el usuario
        currentColor = action.textColor || currentColor;
        currentFontSize = action.fontSize || currentFontSize;
        currentFontFamily = action.fontFamily || currentFontFamily;
    }
    
    // Validar que tenemos valores válidos
    if (x === undefined || y === undefined) {
        console.warn('[Whiteboard] ⚠️ Post-it con coordenadas inválidas:', { x, y, text, width, height });
        return;
    }
    
    // Si no hay texto, usar texto vacío (pero aún así dibujar el post-it)
    if (!text) text = '';
    
    // Asegurar que width y height sean números válidos
    if (!width || width <= 0) width = 200;
    if (!height || height <= 0) height = 150;
    
    const fontSize = Math.max(12, currentFontSize);
    
    // IMPORTANTE: Si no hay acción (creando nuevo post-it), usar SIEMPRE el color actual seleccionado
    // Si hay acción (redibujando desde historial), usar el color guardado en la acción
    let postItColor;
    if (!action) {
        // Creando nuevo post-it: usar el color actual seleccionado
        // Asegurar que currentPostItColor tenga un valor válido
        postItColor = currentPostItColor && currentPostItColor !== 'undefined' && currentPostItColor !== 'null' && currentPostItColor !== '' 
            ? currentPostItColor 
            : '#FFEB3B'; // Fallback a amarillo
        console.log('[Whiteboard] 🆕 Nuevo post-it - usando color actual:', {
            currentPostItColor: currentPostItColor,
            postItColor: postItColor
        });
    } else {
        // Redibujando desde historial: usar el color guardado en la acción
        postItColor = action.backgroundColor || currentPostItColor || '#FFEB3B';
        console.log('[Whiteboard] 🔄 Redibujando post-it - usando color guardado:', {
            actionBackgroundColor: action.backgroundColor,
            currentPostItColor: currentPostItColor,
            postItColor: postItColor
        });
    }
    
    const textColor = action ? (action.textColor || currentColor) : currentColor;
    
    // Validar que el color sea válido
    const finalPostItColor = postItColor && postItColor !== 'undefined' && postItColor !== 'null' && postItColor !== '' ? postItColor : currentPostItColor;
    
    // Log para debugging del color al dibujar
    if (!action || action.type === 'postit') {
        console.log('[Whiteboard] 🎨 Dibujando post-it con color:', {
            finalPostItColor: finalPostItColor,
            postItColor: postItColor,
            currentPostItColor: currentPostItColor,
            actionBackgroundColor: action ? action.backgroundColor : 'sin acción'
        });
    }
    
    // Dibujar fondo del post-it
    // IMPORTANTE: Asegurar que el color sea válido antes de aplicar
    const colorToUse = finalPostItColor || '#FFEB3B'; // Fallback a amarillo si no hay color
    
    // Guardar el estado actual del contexto
    whiteboardCtx.save();
    
    // Aplicar el color de fondo
    whiteboardCtx.fillStyle = colorToUse;
    whiteboardCtx.globalCompositeOperation = 'source-over';
    
    // Log para verificar el color antes de dibujar
    console.log('[Whiteboard] 🎨 Aplicando color de fondo:', {
        colorToUse: colorToUse,
        fillStyle: whiteboardCtx.fillStyle,
        x: x,
        y: y,
        width: width,
        height: height
    });
    
    whiteboardCtx.fillRect(x, y, width, height);
    
    // Verificar que el color se aplicó
    const appliedColor = whiteboardCtx.fillStyle;
    console.log('[Whiteboard] ✅ Color aplicado:', appliedColor);
    
    // Dibujar borde
    whiteboardCtx.strokeStyle = textColor;
    whiteboardCtx.lineWidth = 2;
    whiteboardCtx.strokeRect(x, y, width, height);
    
    // Dibujar texto (cambiar fillStyle para el texto)
    whiteboardCtx.fillStyle = textColor;
    whiteboardCtx.font = `${fontSize}px ${currentFontFamily}`;
    
    if (width && height) {
        const lines = wrapText(text, width - 16, fontSize, currentFontFamily);
        const lineHeight = fontSize * 1.2;
        const startY = y + fontSize + 8;
        
        lines.forEach((line, index) => {
            const lineY = startY + (index * lineHeight);
            if (lineY <= y + height - 8) {
                whiteboardCtx.fillText(line, x + 8, lineY);
            }
        });
    } else {
        whiteboardCtx.fillText(text, x + 8, y + fontSize + 8);
    }
    
    // Si no es una acción existente, crear nueva acción
    if (!action) {
        const actionId = `action_${Date.now()}_${++actionCounter}`;
        const currentUID = getCurrentUID();
        const currentUserName = getCurrentUser();
        const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
        
        // IMPORTANTE: Para nuevos post-its, usar SIEMPRE el color actual seleccionado
        // No usar finalPostItColor porque puede tener un valor antiguo
        const savedBackgroundColor = currentPostItColor; // Usar el color actual seleccionado
        
        const newAction = {
            id: actionId,
            type: 'postit',
            x: x,
            y: y,
            text: text,
            width: width || 200,
            height: height || 150,
            backgroundColor: savedBackgroundColor, // Usar el color actual seleccionado
            textColor: textColor || currentColor,
            fontSize: fontSize,
            fontFamily: currentFontFamily,
            userId: currentUID,
            userName: currentUserName,
            whiteboardMode: currentWhiteboardMode,
            created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico
            created_at_iso: new Date().toISOString()
        };
        
        // Log para debugging del color
        console.log('[Whiteboard] 🎨 Post-it guardado con color:', {
            backgroundColor: newAction.backgroundColor,
            currentPostItColor: currentPostItColor,
            finalPostItColor: finalPostItColor,
            postItColor: postItColor
        });
        
        saveToHistory(newAction);
        lastSentActionId = actionId;
        sentActionIds.add(actionId);
        
        if (sentActionIds.size > 1000) {
            sentActionIds.clear();
            if (lastSentActionId) {
                sentActionIds.add(lastSentActionId);
            }
        }
        
        isCurrentlyDrawing = true;
        showDrawingIndicator(currentUserName);
        
        // Log para debugging
        console.log('[Whiteboard] 📝 Post-it creado y guardado:', {
            id: actionId,
            text: text.substring(0, 20) + '...',
            x, y, width, height,
            mode: currentWhiteboardMode,
            userId: currentUID,
            userName: currentUserName
        });
        
        // Enviar por WebSocket
        console.log('[Whiteboard] 📤 Enviando post-it por WebSocket:', {
            id: actionId,
            websocketConnected: websocketConnected,
            socketReady: whiteboardSocket && whiteboardSocket.readyState === WebSocket.OPEN
        });
        sendDrawingAction(newAction);
        
        // NO redibujar aquí porque drawPostIt ya dibujó el post-it
        // Redibujar causaría que se pierda o se duplique
    }
}

// Borrar post-it
function deletePostIt(postItAction) {
    if (!postItAction || !postItAction.id) {
        console.warn('[Whiteboard] ⚠️ Intento de borrar post-it sin ID válido');
        return;
    }
    
    // Crear acción de borrado
    const actionId = `delete_${Date.now()}_${++actionCounter}`;
    const currentUID = getCurrentUID();
    const currentUserName = getCurrentUser();
    const actionTimestamp = Date.now();
    
    const deleteAction = {
        id: actionId,
        type: 'postit_delete',
        originalId: postItAction.id,
        userId: currentUID,
        userName: currentUserName,
        whiteboardMode: currentWhiteboardMode,
        created_at: actionTimestamp,
        created_at_iso: new Date().toISOString()
    };
    
    // Eliminar del historial local
    const history = userWhiteboards[currentWhiteboardMode].history;
    const postItIndex = history.findIndex(a => a.id === postItAction.id);
    if (postItIndex !== -1) {
        history.splice(postItIndex, 1);
        console.log('[Whiteboard] 🗑️ Post-it eliminado del historial local:', {
            postItId: postItAction.id,
            remainingPostIts: history.filter(a => a.type === 'postit').length
        });
    }
    
    // Redibujar canvas
    redrawFromHistory();
    
    // Guardar acción de borrado en historial (para sincronización)
    saveToHistory(deleteAction);
    lastSentActionId = actionId;
    sentActionIds.add(actionId);
    
    if (sentActionIds.size > 1000) {
        sentActionIds.clear();
        if (lastSentActionId) {
            sentActionIds.add(lastSentActionId);
        }
    }
    
    // Enviar por WebSocket
    console.log('[Whiteboard] 📤 Enviando borrado de post-it por WebSocket:', {
        actionId: actionId,
        originalId: postItAction.id,
        websocketConnected: websocketConnected
    });
    sendDrawingAction(deleteAction);
}

// Limpiar pizarra
function clearWhiteboard() {
    if (!whiteboardCtx || !whiteboardCanvas) return;
    
    // Verificar permisos de edición
    if (!canEditCurrentWhiteboard()) {
        alert('No puedes limpiar esta pizarra. Solo puedes editar la pizarra general o tu propia pizarra.');
        return;
    }
    
    const modeName = currentWhiteboardMode === 'general' ? 'la pizarra general' : 'esta pizarra';
    if (confirm(`¿Estás seguro de que quieres limpiar ${modeName}?`)) {
        whiteboardCtx.clearRect(0, 0, whiteboardCanvas.width, whiteboardCanvas.height);
        
        // Limpiar historial de la pizarra actual
        if (userWhiteboards[currentWhiteboardMode]) {
            userWhiteboards[currentWhiteboardMode].history = [];
        }
        drawingHistory = [];
        historyIndex = -1;
        
        // Crear acción de limpiar con ID
        const actionId = `clear_${Date.now()}_${++actionCounter}`;
        lastSentActionId = actionId;
        sentActionIds.add(actionId);
        
        const currentUID = getCurrentUID();
        const currentUserName = getCurrentUser();
        const actionTimestamp = Date.now(); // Timestamp para ordenamiento cronológico
        
        // Enviar acción de limpiar a otros participantes
        sendDrawingAction({ 
            id: actionId,
            type: 'clear',
            userId: currentUID,
            userName: currentUserName,
            whiteboardMode: currentWhiteboardMode,
            created_at: actionTimestamp, // CRÍTICO: Timestamp cronológico
            created_at_iso: new Date().toISOString()
        });
    }
}

// Guardar dibujo
function saveDrawing() {
    if (!whiteboardCanvas) return;
    
    const dataURL = whiteboardCanvas.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = `pizarra-${Date.now()}.png`;
    link.href = dataURL;
    link.click();
}

// Cargar dibujo guardado
function loadSavedDrawing() {
    const saved = sessionStorage.getItem(`whiteboard_${sessionStorage.getItem('room')}`);
    if (saved) {
        const img = new Image();
        img.onload = function() {
            if (whiteboardCtx && whiteboardCanvas) {
                whiteboardCtx.drawImage(img, 0, 0);
            }
        };
        img.src = saved;
    }
}

// Guardar dibujo en sessionStorage
function autoSaveDrawing() {
    if (!whiteboardCanvas) return;
    const dataURL = whiteboardCanvas.toDataURL('image/png');
    sessionStorage.setItem(`whiteboard_${sessionStorage.getItem('room')}`, dataURL);
}

// Auto-guardar cada 5 segundos
setInterval(autoSaveDrawing, 5000);

// Función para obtener token CSRF (copiada de videocall_chat.js)
function getCSRFToken() {
    const token = document.querySelector('[name=csrf-token]');
    if (token) {
        return token.getAttribute('content');
    }
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    return cookieValue ? cookieValue.split('=')[1] : null;
}

// Obtener usuario actual
function getCurrentUser() {
    if (!currentUser) {
        currentUser = sessionStorage.getItem('name') || window.VIDEOCALL_USER || 'Usuario';
    }
    return currentUser;
}

// Obtener UID actual
function getCurrentUID() {
    // Intentar obtener de múltiples fuentes
    let uid = sessionStorage.getItem('UID');
    
    // Si hay UID en sessionStorage, normalizarlo a string
    if (uid) {
        uid = String(uid).trim();
        if (uid && uid !== 'null' && uid !== 'undefined') {
            // Guardar también en window para referencia rápida
            window.UID = uid;
            return uid;
        }
    }
    
    // Intentar desde window.UID
    if (window.UID) {
        uid = String(window.UID).trim();
        if (uid && uid !== 'null' && uid !== 'undefined') {
        sessionStorage.setItem('UID', uid);
            return uid;
    }
    }
    
    // Intentar obtenerlo del elemento de video local (el que tiene la clase 'local' o está marcado como local)
        const videoElements = document.querySelectorAll('[id^="user-"]');
            for (let elem of videoElements) {
        // Buscar el elemento que tiene la clase 'local' o está marcado como video local
        if (elem.classList.contains('local') || elem.getAttribute('data-local') === 'true') {
                const match = elem.id.match(/user-(\d+)/);
                if (match) {
                uid = String(match[1]).trim();
                    sessionStorage.setItem('UID', uid);
                    window.UID = uid;
                console.log('[Whiteboard] 🔍 UID obtenido del elemento de video local:', uid);
                return uid;
            }
        }
    }
    
    // Si no se encontró, intentar con cualquier elemento de video (último recurso)
    if (!uid && videoElements.length > 0) {
        for (let elem of videoElements) {
            const match = elem.id.match(/user-(\d+)/);
            if (match) {
                uid = String(match[1]).trim();
                sessionStorage.setItem('UID', uid);
                window.UID = uid;
                console.log('[Whiteboard] 🔍 UID obtenido del primer elemento de video encontrado:', uid);
    return uid;
            }
        }
    }
    
    // Si aún no hay UID, log warning
    console.warn('[Whiteboard] ⚠️ No se pudo obtener UID del usuario');
    return null;
}

// Inicializar pizarra de usuario
function initializeUserWhiteboard(userId) {
    if (!userWhiteboards[userId]) {
        userWhiteboards[userId] = {
            history: [],
            canvas: null,
            ctx: null
        };
    }
}

// Cambiar modo de pizarra (general o individual)
function switchWhiteboardMode(mode, userId = null) {
    const currentUID = getCurrentUID();
    console.log('[Whiteboard] 🔄 Cambiando modo de pizarra:', { 
        mode, 
        userId, 
        userIdType: typeof userId,
        currentUID: currentUID,
        currentUIDType: typeof currentUID,
        currentMode: currentWhiteboardMode 
    });
    
    if (mode === 'general') {
        currentWhiteboardMode = 'general';
    } else if (mode === 'user' && userId) {
        // Normalizar userId a string para consistencia
        const normalizedUserId = String(userId);
        currentWhiteboardMode = `user_${normalizedUserId}`;
        initializeUserWhiteboard(currentWhiteboardMode);
        
        // Log para debugging
        console.log('[Whiteboard] 📝 Pizarra de usuario configurada:', {
            userId: normalizedUserId,
            currentUID: String(currentUID),
            isOwner: String(normalizedUserId) === String(currentUID),
            mode: currentWhiteboardMode
        });
    }
    
    // Inicializar la pizarra si no está inicializada
    if (!userWhiteboards[currentWhiteboardMode]) {
        initializeUserWhiteboard(currentWhiteboardMode);
    }
    
    // Redibujar la pizarra actual
    if (whiteboardCanvas && whiteboardCtx) {
        console.log('[Whiteboard] 🎨 Redibujando pizarra:', currentWhiteboardMode);
        redrawFromHistory();
    } else {
        console.warn('[Whiteboard] ⚠️ Canvas no disponible para redibujar');
    }
    
    // Actualizar UI según permisos de edición
    updateWhiteboardEditMode();
    
    // Actualizar UI
    updateWhiteboardSelector();
}

// Actualizar selector de pizarras
function updateWhiteboardSelector() {
    const selector = document.getElementById('whiteboard-mode-selector');
    if (!selector) return;
    
    // Invalidar cache para forzar actualización
    participantsCacheTime = 0;
    
    // Limpiar opciones existentes
    selector.innerHTML = '';
    
    // Opción de pizarra general
    const generalOption = document.createElement('option');
    generalOption.value = 'general';
    generalOption.textContent = '📋 Pizarra General';
    if (currentWhiteboardMode === 'general') {
        generalOption.selected = true;
    }
    selector.appendChild(generalOption);
    
    // Obtener UID del usuario actual
    const currentUID = getCurrentUID();
    const currentUserName = getCurrentUser();
    
    // SIEMPRE agregar la pizarra del usuario actual primero
    if (currentUID) {
        const myOption = document.createElement('option');
        myOption.value = `user_${currentUID}`;
        myOption.textContent = `✏️ ${currentUserName} (Tú)`;
        if (currentWhiteboardMode === `user_${currentUID}`) {
            myOption.selected = true;
        }
        selector.appendChild(myOption);
    }
    
    // Obtener lista de participantes activos (excluyendo al usuario actual)
    const participants = getParticipantsList();
    const addedUIDs = new Set(); // Para evitar duplicados
    
    // Si ya agregamos la pizarra del usuario actual, marcarla
    if (currentUID) {
        addedUIDs.add(String(currentUID));
    }
    
    participants.forEach(participant => {
        const userId = String(participant.uid || participant.id);
        
        // Validar que tenga UID y nombre
        if (!userId || userId === 'null' || userId === 'undefined') {
            return;
        }
        
        // No agregar si es el usuario actual (ya lo agregamos antes)
        if (currentUID && String(userId) === String(currentUID)) {
            return;
        }
        
        // No agregar si ya está en la lista (evitar duplicados)
        if (addedUIDs.has(userId)) {
            return;
        }
        
        const option = document.createElement('option');
        const userName = participant.name || `Usuario ${userId}`;
        option.value = `user_${userId}`;
        option.textContent = `👤 ${userName}`;
        if (currentWhiteboardMode === `user_${userId}`) {
            option.selected = true;
        }
        selector.appendChild(option);
        addedUIDs.add(userId);
    });
}

// Cache de participantes activos (se actualiza desde la API)
let cachedParticipants = [];
let participantsCacheTime = 0;
const PARTICIPANTS_CACHE_DURATION = 5000; // 5 segundos

// Obtener lista de participantes activos desde la API
// IMPORTANTE: Esta función NO debe incluir al usuario actual
function getParticipantsList() {
    const currentUID = getCurrentUID();
    const now = Date.now();
    
    // Si el cache es reciente (menos de 5 segundos), usarlo
    if (cachedParticipants.length > 0 && (now - participantsCacheTime) < PARTICIPANTS_CACHE_DURATION) {
        return filterParticipants(cachedParticipants, currentUID);
    }
    
    // Intentar obtener desde el DOM del panel de participantes primero (más rápido)
    const userItems = document.querySelectorAll('.user-item');
    const participants = [];
    const seenUIDs = new Set();
    
    if (userItems.length > 0) {
        // Usar elementos del DOM si están disponibles (ya filtrados por la API)
    userItems.forEach(item => {
            const uid = item.getAttribute('data-uid');
        const nameElement = item.querySelector('.user-name');
        const name = nameElement ? nameElement.textContent.trim() : null;
        
            // Validar que tenga UID y nombre válidos
            if (uid && uid !== 'null' && uid !== 'undefined' && name && name.trim() !== '') {
                const normalizedUID = String(uid);
                // EXCLUIR al usuario actual - solo agregar otros participantes
                if (currentUID && String(normalizedUID) === String(currentUID)) {
                    return; // Saltar al usuario actual
                }
                
                // Evitar duplicados
                if (!seenUIDs.has(normalizedUID)) {
                    seenUIDs.add(normalizedUID);
                    participants.push({
                        id: normalizedUID,
                        uid: normalizedUID,
                        name: name.trim()
                    });
                }
            }
        });
    }
    
    // TAMBIÉN buscar en los elementos de video (por si el panel de participantes no está actualizado)
    const videoContainers = document.querySelectorAll('[id^="user-container-"]');
    videoContainers.forEach(container => {
        const uidMatch = container.id.match(/user-container-(\d+)/);
        if (uidMatch) {
            const uid = String(uidMatch[1]);
            // Excluir al usuario actual
            if (currentUID && String(uid) === String(currentUID)) {
                return;
            }
            
            // Si ya lo agregamos desde el panel, no duplicar
            if (seenUIDs.has(uid)) {
                return;
            }
            
            // Intentar obtener el nombre del elemento de video
            const nameElement = container.querySelector('.user-name, .username-wrapper .user-name');
            const name = nameElement ? nameElement.textContent.trim() : null;
            
            // Si tiene nombre válido, agregarlo
            if (name && name.trim() !== '' && !name.match(/^Usuario\s+\d+$/)) {
                seenUIDs.add(uid);
            participants.push({
                id: uid,
                uid: uid,
                    name: name.trim()
                });
            } else if (name && name.trim() !== '') {
                // Incluso si es "Usuario X", agregarlo si no está en la lista
                seenUIDs.add(uid);
                participants.push({
                    id: uid,
                    uid: uid,
                    name: name.trim()
                });
            }
        }
    });
    
    // Actualizar cache si encontramos participantes
    if (participants.length > 0) {
        cachedParticipants = participants;
        participantsCacheTime = now;
        return filterParticipants(participants, currentUID);
    }
    
    // Si no hay elementos en el DOM, intentar obtener desde la API directamente
    const roomName = window.VIDEOCALL_ROOM || sessionStorage.getItem('room') || '';
    if (roomName) {
        // Hacer petición async para actualizar cache
        fetchParticipantsFromAPI(roomName, currentUID);
        // Devolver cache existente si hay, o lista vacía
        return cachedParticipants.length > 0 ? filterParticipants(cachedParticipants, currentUID) : [];
    }
    
    return [];
}

// Filtrar participantes: excluir duplicados y usuario actual
function filterParticipants(participants, currentUID) {
    const uniqueParticipants = [];
    const seenUIDs = new Set();
    
    participants.forEach(participant => {
        const uid = String(participant.uid || participant.id);
        
        // Doble verificación: no duplicados y no es el usuario actual
        if (!seenUIDs.has(uid) && (!currentUID || String(uid) !== String(currentUID))) {
            seenUIDs.add(uid);
            uniqueParticipants.push(participant);
        }
    });
    
    return uniqueParticipants;
}

// Obtener participantes desde la API (async, actualiza cache)
function fetchParticipantsFromAPI(roomName, currentUID) {
    fetch(`/videocall/get_participants/${roomName}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al cargar participantes');
            }
            return response.json();
        })
        .then(data => {
            if (data.error || !data.participants) {
                console.warn('[Whiteboard] Error obteniendo participantes:', data.error);
                return;
            }
            
            // Filtrar participantes activos y excluir al usuario actual
            const activeParticipants = data.participants
                .filter(p => p.uid && String(p.uid) !== String(currentUID))
                .map(p => ({
                    id: String(p.uid),
                    uid: String(p.uid),
                    name: p.name || `Usuario ${p.uid}`
                }));
            
            // Actualizar cache
            cachedParticipants = activeParticipants;
            participantsCacheTime = Date.now();
            
            // Actualizar selector si está abierto
            if (typeof updateWhiteboardSelector === 'function') {
                updateWhiteboardSelector();
            }
        })
        .catch(error => {
            console.warn('[Whiteboard] Error obteniendo participantes desde API:', error);
        });
}

// Mostrar indicador de usuario dibujando
function showDrawingIndicator(userName) {
    const indicator = document.getElementById('whiteboard-drawing-indicator');
    if (!indicator) return;
    
    const userNameSpan = indicator.querySelector('.drawing-user-name');
    if (userNameSpan) {
        userNameSpan.textContent = userName;
    }
    
    indicator.classList.add('show');
    
    // Actualizar timestamp
    drawingUsers.set(userName, Date.now());
    
    // Ocultar después de 3 segundos sin actividad
    setTimeout(() => {
        const lastActivity = drawingUsers.get(userName);
        if (lastActivity && Date.now() - lastActivity > 3000) {
            drawingUsers.delete(userName);
            if (drawingUsers.size === 0) {
                indicator.classList.remove('show');
            }
        }
    }, 3000);
}

// Cargar historial de mensajes de pizarra desde el chat
function loadWhiteboardHistoryFromChat() {
    console.log('[Whiteboard] 📥 Cargando historial de pizarra desde chat...');
    
    if (typeof loadChatMessages === 'function') {
        // Cargar mensajes para procesar los de pizarra
        // Esto procesará automáticamente los mensajes WHITEBOARD: y los agregará al historial
        loadChatMessages();
        console.log('[Whiteboard] ✅ Mensajes de chat cargados');
        
        // Después de cargar, ordenar y redibujar desde el historial de la pizarra actual
        // Usar un delay más largo para asegurar que todos los mensajes se procesaron
        setTimeout(() => {
            if (whiteboardCanvas && whiteboardCtx && isWhiteboardOpen) {
                // CRÍTICO: Ordenar el historial de todas las pizarras después de cargar desde el servidor
                // Esto asegura que las acciones estén en orden cronológico correcto
                Object.keys(userWhiteboards).forEach(mode => {
                    const board = userWhiteboards[mode];
                    if (board && board.history && board.history.length > 0) {
                        board.history.sort((a, b) => {
                            const getTimestamp = (action) => {
                                // Prioridad 1: created_at (más confiable)
                                if (action.created_at) {
                                    const ts = typeof action.created_at === 'number' 
                                        ? action.created_at 
                                        : new Date(action.created_at).getTime();
                                    if (!isNaN(ts)) return ts;
                                }
                                // Prioridad 2: messageId
                                if (action.messageId) {
                                    const ts = parseInt(action.messageId);
                                    if (!isNaN(ts)) return ts;
                                }
                                // Prioridad 3: ID de acción
                                if (action.id) {
                                    const parts = action.id.split('_');
                                    if (parts.length >= 2) {
                                        const ts = parseInt(parts[1]);
                                        if (!isNaN(ts)) return ts;
                                    }
                                }
                                // Prioridad 4: timestamp
                                if (action.timestamp) {
                                    const ts = typeof action.timestamp === 'number' 
                                        ? action.timestamp 
                                        : parseInt(action.timestamp);
                                    if (!isNaN(ts)) return ts;
                                }
                                return 0;
                            };
                            const tsA = getTimestamp(a);
                            const tsB = getTimestamp(b);
                            if (tsA === tsB) return 0;
                            return tsA - tsB;
                        });
                    }
                });
                
                console.log('[Whiteboard] 🔄 Redibujando desde historial después de cargar mensajes (ordenado cronológicamente)');
                redrawFromHistory();
            }
        }, 500);
    } else {
        console.warn('[Whiteboard] ⚠️ loadChatMessages no está disponible');
    }
}

// Procesar acciones pendientes cuando la pizarra se abre
function processPendingActions() {
    if (!whiteboardCanvas || !whiteboardCtx || !isWhiteboardOpen) {
        return;
    }
    
    // Obtener el historial de la pizarra actual
    if (!userWhiteboards[currentWhiteboardMode]) {
        initializeUserWhiteboard(currentWhiteboardMode);
    }
    
    const currentBoard = userWhiteboards[currentWhiteboardMode];
    const history = currentBoard.history;
    
    if (history.length === 0) {
        return;
    }
    
    console.log('[Whiteboard] 🔄 Procesando acciones pendientes:', history.length);
    
    // Redibujar desde el historial completo (más eficiente que aplicar una por una)
    redrawFromHistory();
}

// Función para verificar y aplicar acciones pendientes periódicamente cuando la pizarra está abierta
// DESACTIVADA: El sistema de sincronización estaba causando redibujados constantes innecesarios
// Las acciones se aplican inmediatamente cuando llegan si la pizarra está abierta
function startWhiteboardRealtimeSync() {
    // Limpiar cualquier intervalo anterior
    if (window.whiteboardSyncInterval) {
        clearInterval(window.whiteboardSyncInterval);
        window.whiteboardSyncInterval = null;
    }
    
    // Actualizar selector periódicamente para detectar nuevos usuarios (cada 5 segundos)
    if (window.whiteboardSelectorInterval) {
        clearInterval(window.whiteboardSelectorInterval);
    }
    window.whiteboardSelectorInterval = setInterval(() => {
        if (isWhiteboardOpen && typeof updateWhiteboardSelector === 'function') {
            updateWhiteboardSelector();
        }
    }, 5000); // Actualizar cada 5 segundos
    
    // Ya no necesitamos sincronización periódica porque:
    // 1. Las acciones se aplican inmediatamente cuando llegan si la pizarra está abierta
    // 2. Cuando se abre la pizarra, se redibuja todo el historial una vez
    // 3. El polling ya está optimizado para tiempo real (250ms)
    
    console.log('[Whiteboard] ✅ Sincronización en tiempo real activada (sin polling periódico)');
}

// Detener sincronización cuando la pizarra se cierra
function stopWhiteboardRealtimeSync() {
    if (window.whiteboardSyncInterval) {
        clearInterval(window.whiteboardSyncInterval);
        window.whiteboardSyncInterval = null;
    }
    if (window.whiteboardSelectorInterval) {
        clearInterval(window.whiteboardSelectorInterval);
        window.whiteboardSelectorInterval = null;
    }
}

// Abrir/cerrar pizarra
function toggleWhiteboard() {
    const whiteboardPanel = document.getElementById('whiteboard-panel');
    if (!whiteboardPanel) return;
    
    const wasOpen = isWhiteboardOpen;
    isWhiteboardOpen = !isWhiteboardOpen;
    
    if (isWhiteboardOpen) {
        // IMPORTANTE: Establecer isWhiteboardOpen ANTES de cualquier otra operación
        // para que las acciones que lleguen mientras se inicializa se puedan aplicar
        whiteboardPanel.classList.add('open');
        
        // Conectar WebSocket para tiempo real (elimina lag del polling)
        connectWhiteboardWebSocket();
        
        // FALLBACK: Asegurar que el polling de chat esté activo si WebSocket falla
        // para recibir acciones de otros usuarios mientras se inicializa
        if (typeof startChatPolling === 'function') {
            startChatPolling();
        }
        
        // Inicializar inmediatamente (sin setTimeout) para que isWhiteboardOpen y canvas estén listos
        if (!whiteboardCanvas || !whiteboardCtx) {
            // Intentar inicializar inmediatamente
            initializeWhiteboard();
            // Verificar que se inicializó correctamente
            if (whiteboardCanvas && whiteboardCtx) {
                initializeUserWhiteboard('general');
                updateWhiteboardSelector();
                // Cargar historial de mensajes de pizarra
                loadWhiteboardHistoryFromChat();
                // Procesar acciones pendientes después de cargar el historial
                setTimeout(() => {
                    processPendingActions();
                    updateWhiteboardEditMode(); // Actualizar permisos de edición
                }, 300);
                console.log('[Whiteboard] ✅ Pizarra inicializada y lista');
            } else {
                // Si no se pudo inicializar, intentar de nuevo con un pequeño delay
                setTimeout(() => {
                    initializeWhiteboard();
                    if (whiteboardCanvas && whiteboardCtx) {
                        initializeUserWhiteboard('general');
                        updateWhiteboardSelector();
                        loadWhiteboardHistoryFromChat();
                        // Procesar acciones pendientes después de cargar el historial
                        setTimeout(() => {
                            processPendingActions();
                            updateWhiteboardEditMode(); // Actualizar permisos de edición
                        }, 300);
                        console.log('[Whiteboard] ✅ Pizarra inicializada y lista (retry)');
                    } else {
                        console.error('[Whiteboard] ❌ Error inicializando canvas');
                        isWhiteboardOpen = false;
                        whiteboardPanel.classList.remove('open');
                    }
                }, 50);
            }
        } else {
            // Canvas ya inicializado, solo actualizar selector y cargar historial
            initializeUserWhiteboard('general');
            updateWhiteboardSelector();
            loadWhiteboardHistoryFromChat();
            // Procesar acciones pendientes después de cargar el historial
            setTimeout(() => {
                processPendingActions();
                updateWhiteboardEditMode(); // Actualizar permisos de edición
            }, 300);
            console.log('[Whiteboard] ✅ Pizarra abierta (ya inicializada)');
        }
        
        // Iniciar sincronización en tiempo real
        startWhiteboardRealtimeSync();
        
        // Actualizar permisos de edición al abrir
        setTimeout(() => {
            updateWhiteboardEditMode();
        }, 100);
        
        console.log('[Whiteboard] ✅ Pizarra abierta - polling activado, isWhiteboardOpen:', isWhiteboardOpen);
    } else {
        whiteboardPanel.classList.remove('open');
        // Desconectar WebSocket cuando se cierra la pizarra
        disconnectWhiteboardWebSocket();
        // Detener sincronización en tiempo real
        stopWhiteboardRealtimeSync();
        console.log('[Whiteboard] 🔒 Pizarra cerrada');
    }
}

// Actualizar UI según permisos de edición
function updateWhiteboardEditMode() {
    const canEdit = canEditCurrentWhiteboard();
    const canvas = whiteboardCanvas;
    const whiteboardPanel = document.getElementById('whiteboard-panel');
    
    if (!canvas || !whiteboardPanel) return;
    
    // Actualizar cursor del canvas
    if (canEdit) {
        canvas.style.cursor = 'crosshair';
        canvas.style.opacity = '1';
    } else {
        canvas.style.cursor = 'not-allowed';
        canvas.style.opacity = '0.9';
    }
    
    // Mostrar/ocultar indicador de solo lectura
    let readOnlyIndicator = document.getElementById('whiteboard-readonly-indicator');
    if (!canEdit) {
        if (!readOnlyIndicator) {
            readOnlyIndicator = document.createElement('div');
            readOnlyIndicator.id = 'whiteboard-readonly-indicator';
            readOnlyIndicator.textContent = '🔒 Solo lectura - Esta pizarra pertenece a otro usuario';
            readOnlyIndicator.style.cssText = 'position: absolute; top: 10px; left: 50%; transform: translateX(-50%); background: rgba(255, 193, 7, 0.9); color: #000; padding: 8px 16px; border-radius: 4px; font-size: 12px; z-index: 1000; pointer-events: none;';
            whiteboardPanel.appendChild(readOnlyIndicator);
        }
        readOnlyIndicator.style.display = 'block';
    } else {
        if (readOnlyIndicator) {
            readOnlyIndicator.style.display = 'none';
        }
    }
    
    // Deshabilitar/habilitar controles de herramientas
    const toolButtons = document.querySelectorAll('.whiteboard-tool-btn, .whiteboard-color-btn, .whiteboard-width-btn');
    toolButtons.forEach(btn => {
        if (canEdit) {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        } else {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        }
    });
    
    // Deshabilitar/habilitar botón de limpiar
    const clearBtn = document.querySelector('[onclick*="clearWhiteboard"]') || 
                     document.querySelector('.whiteboard-clear-btn');
    if (clearBtn) {
        if (canEdit) {
            clearBtn.disabled = false;
            clearBtn.style.opacity = '1';
            clearBtn.style.cursor = 'pointer';
        } else {
            clearBtn.disabled = true;
            clearBtn.style.opacity = '0.5';
            clearBtn.style.cursor = 'not-allowed';
        }
    }
}

// Manejar cambio de modo de pizarra
function handleWhiteboardModeChange() {
    const selector = document.getElementById('whiteboard-mode-selector');
    if (!selector) return;
    
    const selectedValue = selector.value;
    
    if (selectedValue === 'general') {
        switchWhiteboardMode('general');
    } else if (selectedValue.startsWith('user_')) {
        const userId = selectedValue.replace('user_', '');
        switchWhiteboardMode('user', userId);
    }
    
    // Actualizar UI después del cambio
    updateWhiteboardEditMode();
}

// Exportar funciones y variables globalmente para que el polling pueda detectar el estado
window.toggleWhiteboard = toggleWhiteboard;
window.setTool = setTool;
window.setColor = setColor;
window.setLineWidth = setLineWidth;
window.clearWhiteboard = clearWhiteboard;
window.saveDrawing = saveDrawing;
window.applyDrawingAction = applyDrawingAction;
window.handleWhiteboardModeChange = handleWhiteboardModeChange;
window.switchWhiteboardMode = switchWhiteboardMode;

// Exportar el estado de la pizarra para que el polling pueda optimizarse
Object.defineProperty(window, 'isWhiteboardOpen', {
    get: function() {
        return isWhiteboardOpen;
    },
    enumerable: true,
    configurable: true
});

