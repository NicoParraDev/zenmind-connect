// Gestión de dispositivos y efectos de fondo para videollamadas

let availableDevices = {
    cameras: [],
    microphones: [],
    speakers: []
};

let currentDevices = {
    camera: null,
    microphone: null,
    speaker: null
};

let backgroundBlurEnabled = false;
let backgroundEffect = null;

// Cargar dispositivos disponibles
async function loadDevices() {
    try {
        console.log('[Device Controls] Cargando dispositivos...');
        const devices = await navigator.mediaDevices.enumerateDevices();
        
        console.log('[Device Controls] Dispositivos encontrados:', devices.length);
        
        availableDevices.cameras = devices.filter(d => d.kind === 'videoinput');
        availableDevices.microphones = devices.filter(d => d.kind === 'audioinput');
        availableDevices.speakers = devices.filter(d => d.kind === 'audiooutput');
        
        console.log('[Device Controls] Dispositivos filtrados:', {
            cameras: availableDevices.cameras.length,
            microphones: availableDevices.microphones.length,
            speakers: availableDevices.speakers.length
        });
        
        // Actualizar listas en la UI
        updateDeviceLists();
        
        // Establecer dispositivos actuales solo si no están ya establecidos
        if (availableDevices.cameras.length > 0 && !currentDevices.camera) {
            currentDevices.camera = availableDevices.cameras[0].deviceId;
            updateDeviceName('camera', availableDevices.cameras[0].label || 'Cámara');
        }
        if (availableDevices.microphones.length > 0 && !currentDevices.microphone) {
            currentDevices.microphone = availableDevices.microphones[0].deviceId;
            updateDeviceName('mic', availableDevices.microphones[0].label || 'Micrófono');
        }
        if (availableDevices.speakers.length > 0 && !currentDevices.speaker) {
            currentDevices.speaker = availableDevices.speakers[0].deviceId;
            updateDeviceName('speaker', availableDevices.speakers[0].label || 'Altavoces');
        }
    } catch (error) {
        console.error('[Device Controls] Error cargando dispositivos:', error);
    }
}

// Actualizar listas de dispositivos en la UI
function updateDeviceLists() {
    // Cámaras
    const cameraList = document.getElementById('camera-device-list');
    if (cameraList) {
        cameraList.innerHTML = '';
        if (availableDevices.cameras.length === 0) {
            cameraList.innerHTML = '<div class="device-loading">No se encontraron cámaras</div>';
        } else {
            availableDevices.cameras.forEach(device => {
                const item = document.createElement('div');
                item.className = 'device-item';
                if (device.deviceId === currentDevices.camera) {
                    item.classList.add('active');
                }
                item.innerHTML = `<i class="fas fa-video"></i><span>${device.label || 'Cámara sin nombre'}</span>`;
                item.addEventListener('click', () => selectDevice('camera', device.deviceId, device.label));
                cameraList.appendChild(item);
            });
        }
    }
    
    // Micrófonos
    const micList = document.getElementById('mic-device-list');
    if (micList) {
        micList.innerHTML = '';
        if (availableDevices.microphones.length === 0) {
            micList.innerHTML = '<div class="device-loading">No se encontraron micrófonos</div>';
        } else {
            availableDevices.microphones.forEach(device => {
                const item = document.createElement('div');
                item.className = 'device-item';
                if (device.deviceId === currentDevices.microphone) {
                    item.classList.add('active');
                }
                item.innerHTML = `<i class="fas fa-microphone"></i><span>${device.label || 'Micrófono sin nombre'}</span>`;
                item.addEventListener('click', () => selectDevice('microphone', device.deviceId, device.label));
                micList.appendChild(item);
            });
        }
    }
    
    // Altavoces
    const speakerList = document.getElementById('speaker-device-list');
    if (speakerList) {
        speakerList.innerHTML = '';
        if (availableDevices.speakers.length === 0) {
            speakerList.innerHTML = '<div class="device-loading">No se encontraron altavoces</div>';
        } else {
            availableDevices.speakers.forEach(device => {
                const item = document.createElement('div');
                item.className = 'device-item';
                if (device.deviceId === currentDevices.speaker) {
                    item.classList.add('active');
                }
                item.innerHTML = `<i class="fas fa-volume-up"></i><span>${device.label || 'Altavoz sin nombre'}</span>`;
                item.addEventListener('click', () => selectDevice('speaker', device.deviceId, device.label));
                speakerList.appendChild(item);
            });
        }
    }
}

// Actualizar nombre del dispositivo en el botón
function updateDeviceName(type, name) {
    const nameElement = document.getElementById(`${type}-device-name`);
    if (nameElement) {
        // Truncar nombre si es muy largo
        const maxLength = 20;
        nameElement.textContent = name.length > maxLength ? name.substring(0, maxLength) + '...' : name;
    }
}

// Seleccionar dispositivo
async function selectDevice(type, deviceId, deviceLabel) {
    try {
        if (type === 'camera') {
            currentDevices.camera = deviceId;
            updateDeviceName('camera', deviceLabel);
            // Cambiar cámara en Agora
            // Buscar las variables globales de diferentes formas
            const localTracks = window.localTracks;
            const client = window.client;
            const UID = window.UID || sessionStorage.getItem('UID');
            
            console.log('[Device Controls] Cambiando cámara:', {
                hasLocalTracks: !!localTracks,
                tracksLength: localTracks ? localTracks.length : 0,
                hasClient: !!client,
                UID: UID
            });
            
            if (localTracks && localTracks.length > 1 && localTracks[1] && client) {
                const oldVideoTrack = localTracks[1];
                const newVideoTrack = await AgoraRTC.createCameraVideoTrack({
                    cameraId: deviceId
                });
                
                // Reemplazar track
                await client.unpublish([oldVideoTrack]);
                oldVideoTrack.stop();
                oldVideoTrack.close();
                
                localTracks[1] = newVideoTrack;
                window.localTracks = localTracks; // Actualizar referencia global
                const localVideoPlayer = document.getElementById(`user-${UID}`);
                if (localVideoPlayer) {
                    newVideoTrack.play(localVideoPlayer);
                }
                await client.publish([newVideoTrack]);
            } else {
                console.warn('[Device Controls] No se pudo cambiar la cámara: variables no disponibles');
                throw new Error('Variables de Agora no disponibles');
            }
        } else if (type === 'microphone') {
            currentDevices.microphone = deviceId;
            updateDeviceName('mic', deviceLabel);
            // Cambiar micrófono en Agora
            const localTracks = window.localTracks;
            const client = window.client;
            
            console.log('[Device Controls] Cambiando micrófono:', {
                hasLocalTracks: !!localTracks,
                tracksLength: localTracks ? localTracks.length : 0,
                hasClient: !!client
            });
            
            if (localTracks && localTracks.length > 0 && localTracks[0] && client) {
                const oldAudioTrack = localTracks[0];
                const newAudioTrack = await AgoraRTC.createMicrophoneAudioTrack({
                    microphoneId: deviceId
                });
                
                // Reemplazar track
                await client.unpublish([oldAudioTrack]);
                oldAudioTrack.stop();
                oldAudioTrack.close();
                
                localTracks[0] = newAudioTrack;
                window.localTracks = localTracks; // Actualizar referencia global
                await client.publish([newAudioTrack]);
            } else {
                console.warn('[Device Controls] No se pudo cambiar el micrófono: variables no disponibles');
                throw new Error('Variables de Agora no disponibles');
            }
        } else if (type === 'speaker') {
            currentDevices.speaker = deviceId;
            updateDeviceName('speaker', deviceLabel);
            // Cambiar altavoz (requiere setSinkId en los elementos de audio)
            const audioElements = document.querySelectorAll('audio');
            audioElements.forEach(audio => {
                if (audio.setSinkId) {
                    audio.setSinkId(deviceId).catch(err => {
                        console.warn('Error cambiando altavoz:', err);
                    });
                }
            });
        }
        
        // Actualizar lista
        updateDeviceLists();
        
        // Cerrar dropdown
        closeAllDropdowns();
        
        Swal.fire({
            icon: 'success',
            title: 'Dispositivo cambiado',
            text: `${type === 'camera' ? 'Cámara' : type === 'microphone' ? 'Micrófono' : 'Altavoz'} cambiado exitosamente`,
            timer: 2000,
            showConfirmButton: false,
            toast: true,
            position: 'top-end'
        });
    } catch (error) {
        console.error('Error cambiando dispositivo:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo cambiar el dispositivo. Intenta nuevamente.',
            timer: 3000,
            showConfirmButton: false,
            toast: true,
            position: 'top-end'
        });
    }
}

// Toggle dropdown para controles en barra inferior
function toggleControlDropdown(type) {
    console.log('[Device Controls] toggleControlDropdown llamado con tipo:', type);
    
    // Normalizar el tipo (mic -> mic, camera -> camera)
    const normalizedType = type === 'mic' ? 'mic' : type === 'camera' ? 'camera' : type;
    const btnId = `${normalizedType}-selector-btn`;
    
    console.log('[Device Controls] Buscando botón con ID:', btnId);
    const btn = document.getElementById(btnId);
    
    if (!btn) {
        console.error('[Device Controls] Botón no encontrado:', btnId);
        console.log('[Device Controls] Elementos disponibles:', {
            micBtn: !!document.getElementById('mic-selector-btn'),
            cameraBtn: !!document.getElementById('camera-selector-btn')
        });
        return;
    }
    
    console.log('[Device Controls] Botón encontrado, buscando grupo...');
    const group = btn.closest('.control-with-dropdown');
    if (!group) {
        console.error('[Device Controls] Grupo control-with-dropdown no encontrado para:', type);
        console.log('[Device Controls] Elemento padre del botón:', btn.parentElement);
        return;
    }
    
    console.log('[Device Controls] Grupo encontrado, buscando dropdown...');
    const dropdown = group.querySelector('.control-dropdown');
    if (!dropdown) {
        console.error('[Device Controls] Dropdown no encontrado en el grupo');
        console.log('[Device Controls] Elementos hijos del grupo:', Array.from(group.children).map(c => c.tagName + (c.id ? '#' + c.id : '')));
        return;
    }
    
    console.log('[Device Controls] Dropdown encontrado:', dropdown.id);
    
    const allGroups = document.querySelectorAll('.control-with-dropdown');
    console.log('[Device Controls] Total de grupos encontrados:', allGroups.length);
    
    allGroups.forEach(g => {
        if (g !== group) {
            g.classList.remove('active');
            const otherDropdown = g.querySelector('.control-dropdown');
            if (otherDropdown) {
                otherDropdown.style.display = 'none';
                otherDropdown.style.opacity = '0';
                otherDropdown.style.visibility = 'hidden';
            }
        }
    });
    
    const isActive = group.classList.contains('active');
    console.log('[Device Controls] Estado actual del dropdown:', isActive ? 'abierto' : 'cerrado');
    
    if (isActive) {
        // Cerrar
        console.log('[Device Controls] Cerrando dropdown...');
        group.classList.remove('active');
        dropdown.style.display = 'none';
        dropdown.style.opacity = '0';
        dropdown.style.visibility = 'hidden';
        dropdown.style.transform = 'translateY(10px)';
        console.log('[Device Controls] Dropdown', type, 'cerrado');
    } else {
        // Abrir
        console.log('[Device Controls] Abriendo dropdown...');
        
        // Abrir el dropdown primero
        group.classList.add('active');
        dropdown.style.display = 'block';
        // Forzar reflow para que la animación funcione
        void dropdown.offsetHeight;
        dropdown.style.opacity = '1';
        dropdown.style.visibility = 'visible';
        dropdown.style.transform = 'translateY(0)';
        dropdown.style.pointerEvents = 'auto';
        
        // Verificar que el indicador de audio existe (solo para micrófono)
        if (type === 'mic') {
            const audioIndicator = document.getElementById('mic-audio-level-indicator');
            if (audioIndicator) {
                console.log('[Device Controls] Indicador de audio encontrado, forzando visibilidad...');
                // Forzar todos los estilos necesarios
                audioIndicator.style.cssText = `
                    display: flex !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                    width: 8px !important;
                    height: 32px !important;
                    background: linear-gradient(180deg, rgba(20, 20, 40, 0.95) 0%, rgba(30, 30, 50, 0.95) 100%) !important;
                    border: 2px solid rgba(102, 126, 234, 0.7) !important;
                    border-radius: 4px !important;
                    margin-left: auto !important;
                    margin-right: 10px !important;
                    z-index: 10 !important;
                `;
                console.log('[Device Controls] Estilos aplicados al indicador:', {
                    display: window.getComputedStyle(audioIndicator).display,
                    visibility: window.getComputedStyle(audioIndicator).visibility,
                    opacity: window.getComputedStyle(audioIndicator).opacity,
                    width: window.getComputedStyle(audioIndicator).width,
                    height: window.getComputedStyle(audioIndicator).height
                });
            } else {
                console.warn('[Device Controls] Indicador de audio NO encontrado en el DOM');
            }
        }
        
        // Luego cargar y actualizar dispositivos
        console.log('[Device Controls] Cargando dispositivos...');
        Promise.resolve(loadDevices()).then(() => {
            console.log('[Device Controls] Dispositivos cargados, actualizando listas...');
            updateDeviceLists();
        }).catch(err => {
            console.warn('[Device Controls] Error cargando dispositivos:', err);
            updateDeviceLists(); // Intentar actualizar de todas formas
        });
        
        console.log('[Device Controls] Dropdown', type, 'abierto');
        console.log('[Device Controls] Estilos aplicados:', {
            display: dropdown.style.display,
            opacity: dropdown.style.opacity,
            visibility: dropdown.style.visibility,
            transform: dropdown.style.transform,
            computedDisplay: window.getComputedStyle(dropdown).display,
            computedOpacity: window.getComputedStyle(dropdown).opacity
        });
    }
}

// Toggle dropdown para barra superior (compatibilidad)
function toggleDropdown(type) {
    console.log('[Device Controls] toggleDropdown llamado con tipo:', type);
    const btn = document.getElementById(`${type}-selector-btn`);
    if (!btn) {
        console.error('[Device Controls] Botón no encontrado:', `${type}-selector-btn`);
        return;
    }
    
    const group = btn.closest('.device-selector-group');
    if (!group) {
        console.error('[Device Controls] Grupo no encontrado para:', type);
        return;
    }
    
    const allGroups = document.querySelectorAll('.device-selector-group');
    
    allGroups.forEach(g => {
        if (g !== group) {
            g.classList.remove('active');
        }
    });
    
    const isActive = group.classList.contains('active');
    group.classList.toggle('active');
    
    console.log('[Device Controls] Dropdown', type, isActive ? 'cerrado' : 'abierto');
    
    // Si se abrió, asegurarse de que los dispositivos estén cargados
    if (!isActive) {
        loadDevices();
    }
}

// Cerrar todos los dropdowns
function closeAllDropdowns() {
    document.querySelectorAll('.device-selector-group').forEach(group => {
        group.classList.remove('active');
    });
    document.querySelectorAll('.control-with-dropdown').forEach(group => {
        group.classList.remove('active');
    });
}

// Efecto de blur de fondo
async function toggleBackgroundBlur() {
    try {
        if (!window.localTracks || !window.localTracks[1]) {
            Swal.fire({
                icon: 'warning',
                title: 'Cámara no disponible',
                text: 'Activa la cámara primero para usar efectos de fondo',
                timer: 3000,
                showConfirmButton: false,
                toast: true,
                position: 'top-end'
            });
            return;
        }
        
        backgroundBlurEnabled = !backgroundBlurEnabled;
        const btn = document.getElementById('blur-background-btn');
        
        if (backgroundBlurEnabled) {
            // Aplicar blur usando Agora (si está disponible) o CSS
            btn.classList.add('active');
            // Nota: Agora RTC SDK no tiene soporte nativo para blur de fondo
            // Se puede implementar con TensorFlow.js o similar, pero requiere más trabajo
            Swal.fire({
                icon: 'info',
                title: 'Blur de fondo',
                text: 'Esta funcionalidad requiere configuración adicional. Próximamente.',
                timer: 3000,
                showConfirmButton: false,
                toast: true,
                position: 'top-end'
            });
        } else {
            btn.classList.remove('active');
        }
    } catch (error) {
        console.error('Error aplicando blur:', error);
    }
}

// Panel de fondos y efectos
function openBackgroundEffects() {
    Swal.fire({
        icon: 'info',
        title: 'Fondos y efectos',
        text: 'Esta funcionalidad estará disponible próximamente. Permite cambiar el fondo de tu video.',
        confirmButtonText: 'Entendido'
    });
}

// Inicializar controles de dispositivos
function initializeDeviceControls() {
    console.log('[Device Controls] Inicializando controles de dispositivos...');
    
    // Cargar dispositivos cuando se tenga permiso
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true, audio: true })
            .then(() => {
                console.log('[Device Controls] Permisos obtenidos, cargando dispositivos...');
                loadDevices();
            })
            .catch((err) => {
                console.warn('[Device Controls] Error obteniendo permisos:', err);
                // Cargar dispositivos de todas formas (puede que algunos no requieran permiso)
                loadDevices();
            });
    } else {
        console.warn('[Device Controls] navigator.mediaDevices no disponible');
        // Intentar cargar de todas formas
        loadDevices();
    }
    
    // Event listeners para botones de selección en la barra inferior
    const cameraSelectorBtn = document.getElementById('camera-selector-btn');
    const micSelectorBtn = document.getElementById('mic-selector-btn');
    const speakerBtn = document.getElementById('speaker-selector-btn');
    
    console.log('[Device Controls] Botones encontrados:', {
        camera: !!cameraSelectorBtn,
        mic: !!micSelectorBtn,
        speaker: !!speakerBtn
    });
    
    // Selector de cámara en barra inferior
    if (cameraSelectorBtn) {
        console.log('[Device Controls] Event listener agregado al botón de cámara');
        cameraSelectorBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('[Device Controls] ===== CLICK EN SELECTOR DE CÁMARA =====');
            toggleControlDropdown('camera');
        });
        
        // Test directo: verificar que el botón existe y es clickeable
        console.log('[Device Controls] Botón de cámara verificado:', {
            id: cameraSelectorBtn.id,
            className: cameraSelectorBtn.className,
            parentElement: cameraSelectorBtn.parentElement?.className
        });
    } else {
        console.error('[Device Controls] Botón de cámara no encontrado');
    }
    
    // Selector de micrófono en barra inferior
    if (micSelectorBtn) {
        console.log('[Device Controls] Event listener agregado al botón de micrófono');
        micSelectorBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('[Device Controls] ===== CLICK EN SELECTOR DE MICRÓFONO =====');
            toggleControlDropdown('mic');
        });
        
        // Test directo: verificar que el botón existe y es clickeable
        console.log('[Device Controls] Botón de micrófono verificado:', {
            id: micSelectorBtn.id,
            className: micSelectorBtn.className,
            parentElement: micSelectorBtn.parentElement?.className
        });
    } else {
        console.error('[Device Controls] Botón de micrófono no encontrado');
    }
    
    // Selector de altavoces (solo en barra superior si existe)
    if (speakerBtn) {
        speakerBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('[Device Controls] Click en selector de altavoces');
            toggleDropdown('speaker');
        });
    }
    
    // Cerrar dropdowns al hacer click fuera
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.device-selector-group') && !e.target.closest('.control-with-dropdown')) {
            closeAllDropdowns();
        }
    });
    
    // Botones de efectos de fondo
    const blurBtn = document.getElementById('blur-background-btn');
    const effectsBtn = document.getElementById('background-effects-btn');
    
    if (blurBtn) {
        blurBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('[Device Controls] Click en blur de fondo');
            toggleBackgroundBlur();
        });
    } else {
        console.error('[Device Controls] Botón de blur no encontrado');
    }
    
    if (effectsBtn) {
        effectsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('[Device Controls] Click en efectos de fondo');
            openBackgroundEffects();
        });
    } else {
        console.error('[Device Controls] Botón de efectos no encontrado');
    }
    
    // Botón de configuración
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('[Device Controls] Click en configuración');
            Swal.fire({
                icon: 'info',
                title: 'Configuración',
                text: 'Panel de configuración avanzada. Próximamente.',
                confirmButtonText: 'Entendido'
            });
        });
    } else {
        console.error('[Device Controls] Botón de configuración no encontrado');
    }
    
    // Botones de más opciones
    const moreOptionsBtn = document.getElementById('more-options-btn');
    const moreOptionsRightBtn = document.getElementById('more-options-right-btn');
    const audioSettingsBtn = document.getElementById('audio-settings-btn');
    const ccBtn = document.getElementById('cc-btn');
    
    if (moreOptionsBtn) {
        moreOptionsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('[Device Controls] Click en más opciones (izquierda)');
            Swal.fire({
                icon: 'info',
                title: 'Más opciones',
                text: 'Panel de opciones adicionales. Próximamente.',
                confirmButtonText: 'Entendido'
            });
        });
    }
    
    if (moreOptionsRightBtn) {
        moreOptionsRightBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('[Device Controls] Click en más opciones (derecha)');
            Swal.fire({
                icon: 'info',
                title: 'Más opciones',
                text: 'Panel de opciones adicionales. Próximamente.',
                confirmButtonText: 'Entendido'
            });
        });
    }
    
    if (audioSettingsBtn) {
        audioSettingsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('[Device Controls] Click en configuración de audio');
            // Abrir dropdown de micrófono
            toggleControlDropdown('mic');
        });
    }
    
    if (ccBtn) {
        ccBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            console.log('[Device Controls] Click en subtítulos');
            Swal.fire({
                icon: 'info',
                title: 'Subtítulos',
                text: 'Funcionalidad de subtítulos. Próximamente.',
                confirmButtonText: 'Entendido'
            });
        });
    }
    
    console.log('[Device Controls] Inicialización completada');
    
    // Test directo: verificar que los botones respondan
    setTimeout(() => {
        const testBtn = document.getElementById('camera-selector-btn');
        if (testBtn) {
            console.log('[Device Controls] Test: Botón de cámara encontrado, verificando click...');
            // Simular un click para ver si funciona
            testBtn.addEventListener('click', function testClick() {
                console.log('[Device Controls] TEST: Click en botón de cámara detectado!');
            });
        } else {
            console.error('[Device Controls] TEST: Botón de cámara NO encontrado');
        }
    }, 2000);
}

// Exportar funciones globalmente
window.deviceControls = {
    loadDevices,
    selectDevice,
    toggleBackgroundBlur,
    openBackgroundEffects,
    initializeDeviceControls
};

// Función para verificar si los elementos existen
function checkElementsExist() {
    const elements = {
        topBar: document.getElementById('top-controls-bar'),
        cameraBtn: document.getElementById('camera-selector-btn'),
        micBtn: document.getElementById('mic-selector-btn'),
        speakerBtn: document.getElementById('speaker-selector-btn'),
        blurBtn: document.getElementById('blur-background-btn'),
        effectsBtn: document.getElementById('background-effects-btn'),
        settingsBtn: document.getElementById('settings-btn')
    };
    
    console.log('[Device Controls] Verificando elementos:', elements);
    return elements;
}

// Inicializar cuando el DOM esté listo y después de que se carguen los scripts de Agora
function initDeviceControlsWhenReady() {
    console.log('[Device Controls] Intentando inicializar...');
    
    // Verificar elementos primero
    const elements = checkElementsExist();
    
    if (!elements.topBar) {
        console.warn('[Device Controls] Barra superior no encontrada, reintentando en 500ms...');
        setTimeout(initDeviceControlsWhenReady, 500);
        return;
    }
    
    // Esperar a que el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('[Device Controls] DOM cargado, esperando scripts...');
            // Esperar un poco más para que streams_integrated.js se cargue
            setTimeout(() => {
                console.log('[Device Controls] Inicializando después de DOMContentLoaded...');
                initializeDeviceControls();
            }, 1000);
        });
    } else {
        console.log('[Device Controls] DOM ya listo, esperando scripts...');
        // Esperar un poco más para que streams_integrated.js se cargue
        setTimeout(() => {
            console.log('[Device Controls] Inicializando inmediatamente...');
            initializeDeviceControls();
        }, 1000);
    }
}

// También intentar inicializar cuando la ventana se carga completamente
window.addEventListener('load', () => {
    console.log('[Device Controls] Window loaded, inicializando...');
    setTimeout(() => {
        const elements = checkElementsExist();
        if (elements.topBar) {
            initializeDeviceControls();
        } else {
            console.error('[Device Controls] Elementos no encontrados después de window.load');
        }
    }, 1500);
});

// Intentar múltiples veces para asegurar que se inicialice
let initAttempts = 0;
const maxInitAttempts = 10;

function tryInitialize() {
    initAttempts++;
    console.log(`[Device Controls] Intento de inicialización ${initAttempts}/${maxInitAttempts}`);
    
    const elements = checkElementsExist();
    if (elements.topBar && elements.cameraBtn) {
        console.log('[Device Controls] Elementos encontrados, inicializando...');
        initializeDeviceControls();
    } else if (initAttempts < maxInitAttempts) {
        setTimeout(tryInitialize, 500);
    } else {
        console.error('[Device Controls] No se pudieron encontrar los elementos después de múltiples intentos');
    }
}

// Inicializar inmediatamente si ya está todo listo
initDeviceControlsWhenReady();

// También intentar con un intervalo por si acaso
setTimeout(tryInitialize, 500);

