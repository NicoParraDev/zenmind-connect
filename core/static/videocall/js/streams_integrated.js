/**
 * Agora RTC Streams - Integrado con ZenMindConnect
 * Adaptado para usar variables de entorno y autenticación
 */

// Obtener configuración del servidor (se actualizará dinámicamente)
let APP_ID = null;
let TOKEN = null;
let CHANNEL = null;
let UID = null;
let NAME = null;
let client = null;
let localTracks = [];
let remoteUsers = {};
let isJoining = false;  // Bandera para prevenir múltiples joins
let hasJoined = false;  // Bandera para saber si ya se unió
let screenTracks = null;  // Track de pantalla compartida
let isSharingScreen = false;  // Estado de compartir pantalla

    // Exponer variables globales para acceso desde otros scripts (inicialización temprana)
    window.AgoraVideoCall = {
        localTracks: () => localTracks,
        remoteUsers: () => remoteUsers,
        screenTracks: () => screenTracks,
        isSharingScreen: () => isSharingScreen,
        UID: () => UID
    };

// Función auxiliar para esperar a que expandVideo esté disponible
function waitForExpandVideo(callback, maxAttempts = 20, attempt = 0) {
    if (typeof window.expandVideo === 'function') {
        console.log('expandVideo está disponible, ejecutando callback');
        callback();
    } else if (attempt < maxAttempts) {
        // Esperar 100ms y volver a intentar
        setTimeout(() => {
            waitForExpandVideo(callback, maxAttempts, attempt + 1);
        }, 100);
    } else {
        console.error('expandVideo no está disponible después de', maxAttempts, 'intentos');
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'warning',
                title: 'Función no disponible',
                text: 'La función de expandir video aún no está lista. Por favor, recarga la página.',
                timer: 3000,
                showConfirmButton: false
            });
        } else {
            alert('La función de expandir video aún no está lista. Por favor, recarga la página.');
        }
    }
}

// Función para inicializar variables desde sessionStorage
function initializeSessionData() {
    TOKEN = sessionStorage.getItem('token');
    CHANNEL = sessionStorage.getItem('room');
    UID = sessionStorage.getItem('UID');
    NAME = sessionStorage.getItem('name');
    APP_ID = sessionStorage.getItem('app_id') || APP_ID;
    
    console.log('Datos de sesión:', {
        hasToken: !!TOKEN,
        channel: CHANNEL,
        uid: UID,
        name: NAME,
        appId: APP_ID
    });
    
    return CHANNEL !== null;
}

// Variables para grabación
var video = document.querySelector('.recording');
var output = document.querySelector('.output');
var start = document.querySelector('.start-btn');
var stop = document.querySelector('.stop-btn');
var anc = document.querySelector(".download-anc");
var data = [];

// Función para actualizar el contador de participantes
function updateMemberCount() {
    const memberCountElement = document.getElementById('member-count');
    if (!memberCountElement) {
        console.warn('No se encontró el elemento member-count');
        return;
    }
    
    // Contar los contenedores de video en el DOM
    const videoGrid = document.getElementById('video-grid');
    const videoStreams = document.getElementById('video-streams');
    const container = videoGrid || videoStreams;
    
    if (container) {
        // Contar todos los elementos con id que empiecen con "user-container-"
        const videoContainers = container.querySelectorAll('[id^="user-container-"]');
        const count = videoContainers.length;
        
        // Actualizar el contador
        memberCountElement.textContent = count;
        console.log(`Contador de participantes actualizado: ${count}`);
    } else {
        console.warn('No se encontró el contenedor de videos');
    }
}

// Inicializar cliente Agora
function initializeAgoraClient() {
    if (!client) {
        client = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' });
    }
    return client;
}

// Obtener token de Agora desde el servidor
async function getAgoraToken(channelName) {
    try {
        if (!channelName) {
            throw new Error('Nombre de canal requerido');
        }
        
        console.log('Solicitando token para canal:', channelName);
        const url = `/videocall/get_token/?channel=${encodeURIComponent(channelName)}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || `Error HTTP ${response.status}: ${response.statusText}`;
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        if (!data.token || !data.uid) {
            throw new Error('Respuesta del servidor incompleta. Falta token o UID.');
        }
        
        // Guardar en sessionStorage
        sessionStorage.setItem('token', data.token);
        sessionStorage.setItem('UID', String(data.uid));
        if (data.app_id) {
            APP_ID = data.app_id;
            sessionStorage.setItem('app_id', data.app_id);
        }
        
        console.log('Token obtenido exitosamente');
        
        return {
            token: data.token,
            uid: data.uid,
            appId: data.app_id || APP_ID
        };
    } catch (error) {
        console.error('Error obteniendo token:', error);
        console.error('Detalles:', {
            channelName: channelName,
            message: error.message,
            stack: error.stack
        });
        throw error;
    }
}

// Compartir pantalla
let toggleShare = async () => {
    try {
        if (!isSharingScreen) {
            // Iniciar compartir pantalla
            console.log('Iniciando compartir pantalla...');
            
            // Mostrar notificación
            Swal.fire({
                icon: 'info',
                title: 'Compartiendo pantalla',
                text: 'Selecciona la pantalla o ventana que deseas compartir',
                timer: 3000,
                showConfirmButton: false
            });
            
            // Crear track de pantalla usando Agora
            screenTracks = await AgoraRTC.createScreenVideoTrack({
                encoderConfig: '1080p_1'
            });
            
            // Detener y despublicar el track de cámara local
            if (localTracks[1]) {
                await client.unpublish([localTracks[1]]);
                localTracks[1].stop();
                localTracks[1].close();
            }
            
            // Publicar el track de pantalla
            await client.publish([screenTracks]);
            
            // Reproducir la pantalla compartida en el contenedor local
            const localVideoContainer = document.getElementById(`user-container-${UID}`);
            if (localVideoContainer) {
                const videoPlayer = localVideoContainer.querySelector(`#user-${UID}`);
                if (videoPlayer) {
                    await screenTracks.play(`user-${UID}`);
                }
                
                // Asegurar que el botón de expandir funcione para la pantalla compartida local
                let expandBtn = localVideoContainer.querySelector('.expand-video-btn');
                if (!expandBtn) {
                    expandBtn = document.createElement('button');
                    expandBtn.className = 'expand-video-btn';
                    expandBtn.title = 'Expandir video';
                    expandBtn.innerHTML = '<i class="fas fa-expand"></i><i class="fas fa-compress"></i>';
                    localVideoContainer.appendChild(expandBtn);
                }
                
                // Reconectar el botón de expandir
                const newExpandBtn = expandBtn.cloneNode(true);
                expandBtn.parentNode.replaceChild(newExpandBtn, expandBtn);
                newExpandBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    e.preventDefault();
                    console.log('Botón expandir/comprimir clickeado (pantalla local)');
                    if (localVideoContainer.classList.contains('video-container-expanded')) {
                        if (window.closeExpandedVideo) {
                            window.closeExpandedVideo();
                        }
                    } else {
                        waitForExpandVideo(() => {
                            window.expandVideo(localVideoContainer);
                        });
                    }
                });
                
                // También doble clic
                localVideoContainer.addEventListener('dblclick', function(e) {
                    e.stopPropagation();
                    console.log('Doble clic en pantalla compartida local');
                    if (localVideoContainer.classList.contains('video-container-expanded')) {
                        if (window.closeExpandedVideo) {
                            window.closeExpandedVideo();
                        }
                    } else {
                        waitForExpandVideo(() => {
                            window.expandVideo(localVideoContainer);
                        });
                    }
                });
                localVideoContainer.style.cursor = 'pointer';
            }
            
            isSharingScreen = true;
            
            // Actualizar botón
            const shareBtn = document.getElementById('share-btn') || document.getElementById('screen-share-btn');
            if (shareBtn) {
                shareBtn.classList.add('active');
                shareBtn.title = 'Dejar de compartir pantalla';
            }
            
            // Notificación de éxito
            var toastMixin = Swal.mixin({
                toast: true,
                icon: 'success',
                iconColor: 'white',
                title: 'General Title',
                customClass: {
                    popup: 'colored-toast'
                },
                animation: false,
                position: 'top-right',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer);
                    toast.addEventListener('mouseleave', Swal.resumeTimer);
                }
            });
            toastMixin.fire({
                animation: true,
                title: 'Pantalla compartida exitosamente 💻'
            });
            
            // Escuchar cuando el usuario detiene el compartir desde el navegador
            screenTracks.on('track-ended', async () => {
                console.log('El usuario detuvo el compartir pantalla desde el navegador');
                await stopScreenShare();
            });
            
        } else {
            // Detener compartir pantalla
            await stopScreenShare();
        }
    } catch (error) {
        console.error('Error al compartir pantalla:', error);
        
        // Si el usuario cancela, no mostrar error
        if (error.name === 'NotAllowedError' || error.name === 'AbortError') {
            Swal.fire({
                icon: 'info',
                title: 'Compartir pantalla cancelado',
                text: 'No se compartió la pantalla',
                timer: 2000,
                showConfirmButton: false
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error al compartir pantalla',
                text: error.message || 'Ocurrió un error al intentar compartir la pantalla',
                confirmButtonText: 'Entendido'
            });
        }
        
        // Asegurar que el estado esté correcto
        isSharingScreen = false;
        const shareBtn = document.getElementById('share-btn') || document.getElementById('screen-share-btn');
        if (shareBtn) {
            shareBtn.classList.remove('active');
            shareBtn.title = 'Compartir pantalla';
        }
    }
};

// Función para detener compartir pantalla
let stopScreenShare = async () => {
    try {
        console.log('Deteniendo compartir pantalla...');
        
        // Despublicar el track de pantalla
        if (screenTracks) {
            await client.unpublish([screenTracks]);
            screenTracks.stop();
            screenTracks.close();
            screenTracks = null;
        }
        
        // Volver a crear y publicar el track de cámara
        if (localTracks.length > 0 && localTracks[0]) {
            // El audio ya está disponible
            localTracks[1] = await AgoraRTC.createCameraVideoTrack();
            await client.publish([localTracks[1]]);
            
            // Reproducir la cámara en el contenedor local
            const localVideoContainer = document.getElementById(`user-container-${UID}`);
            if (localVideoContainer) {
                const videoPlayer = localVideoContainer.querySelector(`#user-${UID}`);
                if (videoPlayer) {
                    await localTracks[1].play(`user-${UID}`);
                }
                
                // Asegurar que el botón de expandir funcione cuando se restaura la cámara
                let expandBtn = localVideoContainer.querySelector('.expand-video-btn');
                if (!expandBtn) {
                    expandBtn = document.createElement('button');
                    expandBtn.className = 'expand-video-btn';
                    expandBtn.title = 'Expandir video';
                    expandBtn.innerHTML = '<i class="fas fa-expand"></i><i class="fas fa-compress"></i>';
                    localVideoContainer.appendChild(expandBtn);
                }
                
                // Reconectar el botón de expandir
                const newExpandBtn = expandBtn.cloneNode(true);
                expandBtn.parentNode.replaceChild(newExpandBtn, expandBtn);
                newExpandBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    e.preventDefault();
                    console.log('Botón expandir/comprimir clickeado (local - cámara restaurada)');
                    if (localVideoContainer.classList.contains('video-container-expanded')) {
                        if (window.closeExpandedVideo) {
                            window.closeExpandedVideo();
                        }
                    } else {
                        waitForExpandVideo(() => {
                            window.expandVideo(localVideoContainer);
                        });
                    }
                });
                
                // También doble clic
                localVideoContainer.addEventListener('dblclick', function(e) {
                    e.stopPropagation();
                    console.log('Doble clic en video local (cámara restaurada)');
                    if (localVideoContainer.classList.contains('video-container-expanded')) {
                        if (window.closeExpandedVideo) {
                            window.closeExpandedVideo();
                        }
                    } else {
                        waitForExpandVideo(() => {
                            window.expandVideo(localVideoContainer);
                        });
                    }
                });
                localVideoContainer.style.cursor = 'pointer';
            }
        }
        
        isSharingScreen = false;
        
        // Actualizar botón
        const shareBtn = document.getElementById('share-btn') || document.getElementById('screen-share-btn');
        if (shareBtn) {
            shareBtn.classList.remove('active');
            shareBtn.title = 'Compartir pantalla';
        }
        
        // Notificación
        var toastMixin = Swal.mixin({
            toast: true,
            icon: 'info',
            iconColor: 'white',
            title: 'General Title',
            customClass: {
                popup: 'colored-toast'
            },
            animation: false,
            position: 'top-right',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });
        toastMixin.fire({
            animation: true,
            title: 'Dejaste de compartir pantalla 💻'
        });
        
    } catch (error) {
        console.error('Error al detener compartir pantalla:', error);
        isSharingScreen = false;
    }
};

// Unirse y mostrar stream local
let joinAndDisplayLocalStream = async () => {
    // Prevenir múltiples llamadas simultáneas
    if (isJoining) {
        console.warn('Ya se está intentando unir a la sala, esperando...');
        return;
    }
    
    if (hasJoined) {
        console.warn('Ya se unió a la sala anteriormente');
        return;
    }
    
    // Inicializar datos de sesión si no están cargados
    if (!CHANNEL) {
        if (!initializeSessionData()) {
            console.error('No hay canal definido en sessionStorage');
            return;
        }
    }
    
    if (!CHANNEL) {
        console.error('No se pudo obtener el canal');
        return;
    }
    
    const roomNameElement = document.getElementById('room-name');
    if (roomNameElement) {
        roomNameElement.innerText = CHANNEL;
    }
    
    // Marcar que estamos intentando unirnos
    isJoining = true;
    
    // Inicializar cliente solo si no existe
    if (!client) {
        client = initializeAgoraClient();
        client.on('user-published', handleUserJoined);
        client.on('user-unpublished', handleUserUnpublished);
        client.on('user-left', handleUserLeft);
    } else {
        // Si el cliente ya existe y está conectado, no hacer nada
        const connectionState = client.connectionState;
        if (connectionState === 'CONNECTING' || connectionState === 'CONNECTED') {
            console.warn('Cliente ya está conectando/conectado. Estado:', connectionState);
            isJoining = false;
            return;
        }
    }

    try {
        // SIEMPRE obtener un token nuevo para evitar tokens expirados
        // Los tokens de Agora tienen un tiempo de expiración y pueden causar errores
        console.log('Obteniendo token nuevo de Agora para canal:', CHANNEL);
        const tokenData = await getAgoraToken(CHANNEL);
        TOKEN = tokenData.token;
        UID = tokenData.uid;
        if (tokenData.appId) {
            APP_ID = tokenData.appId;
        }
        console.log('Token obtenido exitosamente. UID:', UID);
        
        // Guardar en sessionStorage para referencia, pero siempre obtener uno nuevo
        if (TOKEN) {
            sessionStorage.setItem('TOKEN', TOKEN);
        }
        if (UID) {
            sessionStorage.setItem('UID', String(UID));
        }
        if (APP_ID) {
            sessionStorage.setItem('APP_ID', APP_ID);
        }
        
        // Validar que tenemos todo lo necesario
        if (!APP_ID) {
            throw new Error('APP_ID no está disponible. Verifica la configuración de Agora.');
        }
        
        if (!TOKEN) {
            throw new Error('Token no disponible. No se pudo obtener el token de Agora.');
        }
        
        console.log('Uniéndose a la sala con:', {
            appId: APP_ID,
            channel: CHANNEL,
            uid: UID,
            hasToken: !!TOKEN
        });
        
        UID = await client.join(APP_ID, CHANNEL, TOKEN, UID);
        console.log('Unido exitosamente a la sala. UID final:', UID);
        hasJoined = true;
        isJoining = false;
    } catch (error) {
        isJoining = false;  // Resetear bandera en caso de error
        console.error('Error uniéndose a la sala:', error);
        console.error('Detalles del error:', {
            message: error.message,
            stack: error.stack,
            appId: APP_ID,
            channel: CHANNEL,
            hasToken: !!TOKEN
        });
        
        // Mostrar mensaje más descriptivo
        let errorMessage = 'Error al unirse a la videollamada. ';
        if (error.message) {
            errorMessage += error.message;
        } else {
            errorMessage += 'Por favor, recarga la página.';
        }
        
        Swal.fire({
            icon: 'error',
            title: 'Error de conexión',
            text: errorMessage,
            confirmButtonText: 'Recargar',
            allowOutsideClick: false
        }).then(() => {
            window.location.reload();
        });
        return;
    }

    try {
        localTracks = await AgoraRTC.createMicrophoneAndCameraTracks();
        console.log('Tracks de cámara y micrófono creados exitosamente');
    } catch (error) {
        console.error('Error creando tracks:', error);
        isJoining = false;  // Resetear bandera
        Swal.fire({
            icon: 'error',
            title: 'Error de permisos',
            text: 'Error al acceder a cámara/micrófono. Verifica los permisos del navegador.',
            confirmButtonText: 'Entendido'
        });
        return;
    }

    // Crear miembro en el servidor
    let member = await createMember();

    // Obtener iniciales del nombre
    const getInitials = (name) => {
        if (!name) return '?';
        const parts = name.trim().split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return name[0].toUpperCase();
    };
    
    const initials = getInitials(member.name);
    
    let player = `<div class="video-container local-video-item" id="user-container-${UID}">
                     <div class="video-player" id="user-${UID}">
                         <div class="camera-off-placeholder" style="display: none;">
                             <div class="user-initials" data-initials="${initials}">${initials}</div>
                         </div>
                     </div>
                     <div class="username-wrapper"><span class="user-name">${member.name} (Tú)</span></div>
                     <button class="expand-video-btn" title="Expandir video">
                         <i class="fas fa-expand"></i>
                         <i class="fas fa-compress"></i>
                     </button>
                     <video class="recording" id="recording" autoplay muted width="300px" height="300px" style="display: none;"></video>
                  </div>`;

    // Buscar contenedor de videos (video-grid o video-streams)
    const videoGrid = document.getElementById('video-grid');
    const videoStreams = document.getElementById('video-streams');
    const videoContainer = videoGrid || videoStreams;
    
    if (videoContainer) {
        videoContainer.insertAdjacentHTML('beforeend', player);
        console.log('Reproduciendo video local en elemento:', `user-${UID}`);
        await localTracks[1].play(`user-${UID}`);
        console.log('Video local reproducido, publicando tracks...');
        await client.publish([localTracks[0], localTracks[1]]);
        console.log('Tracks publicados exitosamente');
        // Actualizar contador de participantes
        updateMemberCount();
        
        // Conectar botón de expandir después de insertar en el DOM
        const localContainer = document.getElementById(`user-container-${UID}`);
        if (localContainer) {
            // Asegurar que el botón de expandir exista y funcione
            let expandBtn = localContainer.querySelector('.expand-video-btn');
            if (!expandBtn) {
                expandBtn = document.createElement('button');
                expandBtn.className = 'expand-video-btn';
                expandBtn.title = 'Expandir video';
                expandBtn.innerHTML = '<i class="fas fa-expand"></i><i class="fas fa-compress"></i>';
                localContainer.appendChild(expandBtn);
            }
            
            // Reconectar el botón de expandir (remover listeners anteriores y agregar nuevos)
            const newExpandBtn = expandBtn.cloneNode(true);
            expandBtn.parentNode.replaceChild(newExpandBtn, expandBtn);
            newExpandBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                console.log('Botón expandir/comprimir clickeado (local)');
                if (localContainer.classList.contains('video-container-expanded')) {
                    if (window.closeExpandedVideo) {
                        window.closeExpandedVideo();
                    }
                } else {
                    waitForExpandVideo(() => {
                        window.expandVideo(localContainer);
                    });
                }
            });
            
            // También doble clic
            localContainer.addEventListener('dblclick', function(e) {
                e.stopPropagation();
                console.log('Doble clic en video local');
                if (localContainer.classList.contains('video-container-expanded')) {
                    if (window.closeExpandedVideo) {
                        window.closeExpandedVideo();
                    }
                } else {
                    waitForExpandVideo(() => {
                        window.expandVideo(localContainer);
                    });
                }
            });
            localContainer.style.cursor = 'pointer';
        }
    } else {
        console.error('No se encontró contenedor de videos');
    }
};

// Manejar usuario que se une
let handleUserJoined = async (user, mediaType) => {
    remoteUsers[user.uid] = user;
    await client.subscribe(user, mediaType);

    if (mediaType === 'video') {
        // Verificar si ya existe un contenedor para este usuario
        let player = document.getElementById(`user-container-${user.uid}`);
        let isNewContainer = false;
        
        if (player == null) {
            // Crear nuevo contenedor solo si no existe
            let member = await getMember(user);
            
            // Obtener iniciales del nombre
            const getInitials = (name) => {
                if (!name) return '?';
                const parts = name.trim().split(' ');
                if (parts.length >= 2) {
                    return (parts[0][0] + parts[1][0]).toUpperCase();
                }
                return name[0].toUpperCase();
            };
            
            const initials = getInitials(member.name);
            
        player = `
            <div class="video-container" id="user-container-${user.uid}">
                <div class="video-player" id="user-${user.uid}">
                    <div class="camera-off-placeholder" style="display: none;">
                        <div class="user-initials" data-initials="${initials}">${initials}</div>
                    </div>
                </div>
                <div class="username-wrapper"><span class="user-name">${member.name}</span></div>
                <button class="expand-video-btn" title="Expandir video">
                    <i class="fas fa-expand"></i>
                    <i class="fas fa-compress"></i>
                </button>
                <button class="mute-remote-btn" title="Mutear/Desmutear audio" data-uid="${user.uid}">
                    <i class="fas fa-volume-up"></i>
                </button>
            </div> 
        `;
            isNewContainer = true;
        } else {
            // Si el contenedor ya existe, limpiar el video player para actualizar el track
            const videoPlayer = player.querySelector(`#user-${user.uid}`);
            if (videoPlayer) {
                videoPlayer.innerHTML = ''; // Limpiar para que el nuevo track se reproduzca
            }
        }

        // Buscar contenedor de videos (video-grid o video-streams)
        const videoGrid = document.getElementById('video-grid');
        const videoStreams = document.getElementById('video-streams');
        const videoContainer = videoGrid || videoStreams;
        
        if (videoContainer) {
            // Solo agregar al DOM si es un nuevo contenedor
            if (isNewContainer) {
                videoContainer.insertAdjacentHTML('beforeend', player);
            }
            
            console.log('Reproduciendo video remoto en elemento:', `user-${user.uid}`);
            console.log('Tipo de track:', user.videoTrack.getTrackLabel ? user.videoTrack.getTrackLabel() : 'video');
            
            // Reproducir el track de video (puede ser cámara o pantalla compartida)
            await user.videoTrack.play(`user-${user.uid}`);
            console.log('Video remoto reproducido exitosamente');
            
            // Ocultar placeholder cuando el video se reproduce (cámara encendida)
            const remoteVideoPlayer = document.getElementById(`user-${user.uid}`);
            if (remoteVideoPlayer) {
                remoteVideoPlayer.classList.remove('camera-off');
                const placeholder = remoteVideoPlayer.querySelector('.camera-off-placeholder');
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
                const videoElement = remoteVideoPlayer.querySelector('video');
                if (videoElement) {
                    videoElement.style.display = 'block';
                }
            }
            
            // Escuchar cambios en el estado del track de video
            if (user.videoTrack) {
                user.videoTrack.on('track-ended', () => {
                    const remoteVideoPlayer = document.getElementById(`user-${user.uid}`);
                    if (remoteVideoPlayer) {
                        remoteVideoPlayer.classList.add('camera-off');
                        const placeholder = remoteVideoPlayer.querySelector('.camera-off-placeholder');
                        if (placeholder) {
                            placeholder.style.display = 'flex';
                        }
                        const videoElement = remoteVideoPlayer.querySelector('video');
                        if (videoElement) {
                            videoElement.style.display = 'none';
                        }
                    }
                });
            }
            
            // Actualizar contador de participantes
            updateMemberCount();
            
            // Conectar botones después de insertar en el DOM (SIEMPRE, incluso si el contenedor ya existe)
            const remoteContainer = document.getElementById(`user-container-${user.uid}`);
            if (remoteContainer) {
                // Asegurar que el contenedor tenga los botones necesarios
                let expandBtn = remoteContainer.querySelector('.expand-video-btn');
                if (!expandBtn) {
                    // Si no existe, crearlo
                    expandBtn = document.createElement('button');
                    expandBtn.className = 'expand-video-btn';
                    expandBtn.title = 'Expandir video';
                    expandBtn.innerHTML = '<i class="fas fa-expand"></i><i class="fas fa-compress"></i>';
                    remoteContainer.appendChild(expandBtn);
                }
                
                // Reconectar el botón de expandir/comprimir (remover listeners anteriores y agregar nuevos)
                const newExpandBtn = expandBtn.cloneNode(true);
                expandBtn.parentNode.replaceChild(newExpandBtn, expandBtn);
                newExpandBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    e.preventDefault();
                    console.log('Botón expandir/comprimir clickeado (remoto)');
                    // Verificar si el contenedor está expandido
                    if (remoteContainer.classList.contains('video-container-expanded')) {
                        if (window.closeExpandedVideo) {
                            window.closeExpandedVideo();
                        }
                    } else {
                        waitForExpandVideo(() => {
                            window.expandVideo(remoteContainer);
                        });
                    }
                });
                // También doble clic
                remoteContainer.addEventListener('dblclick', function(e) {
                    e.stopPropagation();
                    console.log('Doble clic en video remoto');
                    if (remoteContainer.classList.contains('video-container-expanded')) {
                        if (window.closeExpandedVideo) {
                            window.closeExpandedVideo();
                        }
                    } else {
                        waitForExpandVideo(() => {
                            window.expandVideo(remoteContainer);
                        });
                    }
                });
                remoteContainer.style.cursor = 'pointer';
                
                // Botón de mute individual
                let muteBtn = remoteContainer.querySelector('.mute-remote-btn');
                if (!muteBtn) {
                    // Si no existe, crearlo (solo para usuarios remotos)
                    const currentUID = sessionStorage.getItem('UID') || (window.AgoraVideoCall ? window.AgoraVideoCall.UID() : null);
                    if (user.uid !== currentUID && user.uid !== String(currentUID)) {
                        muteBtn = document.createElement('button');
                        muteBtn.className = 'mute-remote-btn';
                        muteBtn.title = 'Mutear/Desmutear audio';
                        muteBtn.setAttribute('data-uid', user.uid);
                        muteBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
                        remoteContainer.appendChild(muteBtn);
                    }
                }
                
                if (muteBtn) {
                    // Reconectar el botón de mute (remover listeners anteriores y agregar nuevos)
                    const newMuteBtn = muteBtn.cloneNode(true);
                    muteBtn.parentNode.replaceChild(newMuteBtn, muteBtn);
                    newMuteBtn.addEventListener('click', function(e) {
                        e.stopPropagation();
                        e.preventDefault();
                        console.log('Botón mute clickeado para usuario:', user.uid);
                        toggleRemoteMute(user.uid, newMuteBtn);
                    });
                }
            }
        } else {
            console.error('No se encontró contenedor de videos para video remoto');
        }
    }

    if (mediaType === 'audio') {
        user.audioTrack.play();
        // Actualizar contador incluso si solo es audio
        updateMemberCount();
    }
};

// Manejar usuario que se va
let handleUserUnpublished = async (user, mediaType) => {
    if (mediaType === 'video') {
        const remoteVideoPlayer = document.getElementById(`user-${user.uid}`);
        if (remoteVideoPlayer) {
            remoteVideoPlayer.classList.add('camera-off');
            const placeholder = remoteVideoPlayer.querySelector('.camera-off-placeholder');
            if (placeholder) {
                placeholder.style.display = 'flex';
            }
            const videoElement = remoteVideoPlayer.querySelector('video');
            if (videoElement) {
                videoElement.style.display = 'none';
            }
        }
    }
};

let handleUserLeft = async (user) => {
    var toastMixin = Swal.mixin({
        toast: true,
        icon: 'error',
        iconColor: 'white',
        title: 'General Title',
        customClass: {
            popup: 'colored-toast'
        },
        animation: false,
        position: 'top-right',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer);
            toast.addEventListener('mouseleave', Swal.resumeTimer);
        }
    });
    toastMixin.fire({
        animation: true,
        title: 'Un usuario se fué de la sala 🛋️'
    });

    var audioEl = document.getElementById("audio3");
    if (audioEl) {
        audioEl.play().catch(err => console.log('Error reproduciendo audio de salida:', err));
    }
    
    delete remoteUsers[user.uid];
    const userContainer = document.getElementById(`user-container-${user.uid}`);
    if (userContainer) userContainer.remove();
    // Actualizar contador de participantes
    updateMemberCount();
};

// Salir y remover stream local
let leaveAndRemoveLocalStream = async () => {
    Swal.fire({
        backdrop: "linear-gradient(white, green)",
        title: 'Esperamos que vuelvas pronto',
        text: 'Gracias por querer ser participe de esta nueva iniciativa!',
        showCancelButton: false,
        showConfirmButton: false,
        footer: '<span class="verde">Tu puedes, no estas solo</span>',
        padding: '1rem',
    });
    
    for (let i = 0; localTracks.length > i; i++) {
        localTracks[i].stop();
        localTracks[i].close();
    }
    
    await client.leave();
    deleteMember();
    window.open('/', '_self');
};

// Toggle cámara
let toggleCamera = async (e) => {
    console.log('TOGGLE CAMERA TRIGGERED');
    if (!localTracks || localTracks.length < 2 || !localTracks[1]) {
        console.warn('No hay track de video disponible aún. Esperando...');
        // Mostrar mensaje al usuario
        Swal.fire({
            icon: 'info',
            title: 'Cámara no lista',
            text: 'Espera un momento mientras se inicializa la cámara.',
            timer: 2000,
            showConfirmButton: false
        });
        return;
    }
    
    const button = e.target.closest('button') || e.target;
    const icon = button ? button.querySelector('i') : null;
    
    if (localTracks[1].muted) {
        var toastMixin = Swal.mixin({
            toast: true,
            icon: 'info',
            iconColor: 'white',
            title: 'General Title',
            customClass: {
                popup: 'colored-toast'
            },
            animation: false,
            position: 'top-right',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });
        toastMixin.fire({
            animation: true,
            title: 'Cámara encendida 🎥'
        });

        var audioEl = document.getElementById("audio6");
        if (audioEl) {
            audioEl.play().catch(err => console.log('Error reproduciendo audio:', err));
        }

        await localTracks[1].setMuted(false);
        if (button) {
            button.classList.add('active');
            button.style.backgroundColor = '#10b981';
            button.style.color = '#fff';
        }
        if (icon) {
            icon.className = 'fas fa-video';
        }
        
        // Ocultar placeholder cuando la cámara está encendida
        const localVideoPlayer = document.getElementById(`user-${UID}`);
        if (localVideoPlayer) {
            localVideoPlayer.classList.remove('camera-off');
            const placeholder = localVideoPlayer.querySelector('.camera-off-placeholder');
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            // Mostrar el video
            const videoElement = localVideoPlayer.querySelector('video');
            if (videoElement) {
                videoElement.style.display = 'block';
            }
        }
    } else {
        var toastMixin = Swal.mixin({
            toast: true,
            icon: 'warning',
            iconColor: 'white',
            title: 'General Title',
            customClass: {
                popup: 'colored-toast'
            },
            animation: false,
            position: 'top-right',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });
        toastMixin.fire({
            animation: true,
            title: 'Cámara apagada 🎥'
        });

        var audioEl = document.getElementById("audio5");
        if (audioEl) {
            audioEl.play().catch(err => console.log('Error reproduciendo audio:', err));
        }

        await localTracks[1].setMuted(true);
        if (button) {
            button.classList.remove('active');
            button.style.backgroundColor = 'rgb(255, 80, 80)';
            button.style.color = '#fff';
        }
        if (icon) {
            icon.className = 'fas fa-video-slash';
        }
        
        // Mostrar placeholder cuando la cámara está apagada
        const localVideoPlayer = document.getElementById(`user-${UID}`);
        if (localVideoPlayer) {
            localVideoPlayer.classList.add('camera-off');
            const placeholder = localVideoPlayer.querySelector('.camera-off-placeholder');
            if (placeholder) {
                placeholder.style.display = 'flex';
            }
            // Ocultar el video
            const videoElement = localVideoPlayer.querySelector('video');
            if (videoElement) {
                videoElement.style.display = 'none';
            }
        }
    }
};

// Toggle micrófono
let toggleMic = async (e) => {
    if (!localTracks || localTracks.length < 1 || !localTracks[0]) {
        console.warn('No hay track de audio disponible aún. Esperando...');
        // Mostrar mensaje al usuario
        Swal.fire({
            icon: 'info',
            title: 'Micrófono no listo',
            text: 'Espera un momento mientras se inicializa el micrófono.',
            timer: 2000,
            showConfirmButton: false
        });
        return;
    }
    
    const button = e.target.closest('button') || e.target;
    const icon = button ? button.querySelector('i') : null;
    
    if (localTracks[0].muted) {
        var toastMixin = Swal.mixin({
            toast: true,
            icon: 'info',
            iconColor: 'white',
            title: 'General Title',
            customClass: {
                popup: 'colored-toast'
            },
            animation: false,
            position: 'top-right',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });
        toastMixin.fire({
            animation: true,
            title: 'Micrófono encendido 🎙️'
        });

        var audioEl = document.getElementById("audio6");
        if (audioEl) {
            audioEl.play().catch(err => console.log('Error reproduciendo audio:', err));
        }

        await localTracks[0].setMuted(false);
        if (button) {
            button.classList.add('active');
            button.style.backgroundColor = '#10b981';
            button.style.color = '#fff';
        }
        if (icon) {
            icon.className = 'fas fa-microphone';
        }
    } else {
        var toastMixin = Swal.mixin({
            toast: true,
            icon: 'warning',
            iconColor: 'white',
            title: 'General Title',
            customClass: {
                popup: 'colored-toast'
            },
            animation: false,
            position: 'top-right',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });
        toastMixin.fire({
            animation: true,
            title: 'Micrófono apagado 🎙️'
        });

        var audioEl = document.getElementById("audio5");
        if (audioEl) {
            audioEl.play().catch(err => console.log('Error reproduciendo audio:', err));
        }

        await localTracks[0].setMuted(true);
        if (button) {
            button.classList.remove('active');
            button.style.backgroundColor = 'rgb(255, 80, 80)';
            button.style.color = '#fff';
        }
        if (icon) {
            icon.className = 'fas fa-microphone-slash';
        }
    }
};

// Crear miembro
let createMember = async () => {
    try {
        const csrfToken = getCSRFToken();
        if (!csrfToken) {
            throw new Error('No se pudo obtener el token CSRF. Por favor, recarga la página.');
        }
        
        const response = await fetch('/videocall/create_member/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ 'name': NAME, 'room_name': CHANNEL, 'UID': UID })
        });
        
        // Verificar si la respuesta es JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Respuesta no JSON del servidor:', text.substring(0, 200));
            throw new Error(`Error del servidor (${response.status}): La respuesta no es JSON. Verifica los logs del servidor.`);
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `Error HTTP ${response.status}` }));
            throw new Error(errorData.error || `Error HTTP ${response.status}`);
        }
        
        const member = await response.json();

        var toastMixin = Swal.mixin({
            toast: true,
            icon: 'success',
            iconColor: 'white',
            title: 'General Title',
            customClass: {
                popup: 'colored-toast'
            },
            animation: false,
            position: 'top-right',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });
        toastMixin.fire({
            animation: true,
            title: (NAME || 'Usuario') + ' Has ingresado a la sala 🛋️',
        });
        var audioEl = document.getElementById("audio");
        if (audioEl) audioEl.play();
        return member;
    } catch (error) {
        console.error('Error creando miembro:', error);
        // No lanzar el error, solo loguearlo para que la videollamada continúe
        // El usuario ya está en la sala de Agora, solo falta el registro en la BD
        return {
            name: NAME || 'Usuario',
            role: 'paciente',
            created: false
        };
    }
};

// Obtener miembro
let getMember = async (user) => {
    let response = await fetch(`/videocall/get_member/?UID=${user.uid}&room_name=${CHANNEL}`);
    let member = await response.json();

    var toastMixin = Swal.mixin({
        toast: true,
        icon: 'info',
        iconColor: 'white',
        title: 'General Title',
        customClass: {
            popup: 'colored-toast'
        },
        animation: false,
        position: 'top-right',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer);
            toast.addEventListener('mouseleave', Swal.resumeTimer);
        }
    });
    toastMixin.fire({
        animation: true,
        title: 'Un usuario llegó a la sala 👤➕'
    });

    var audioEl = document.getElementById("audio2");
    if (audioEl) {
        audioEl.play().catch(err => console.log('Error reproduciendo audio de entrada:', err));
    }
    return member;
};

// Eliminar miembro
let deleteMember = async () => {
    alert('⬅️ Has salido de la sala ⬅️');
    let response = await fetch('/videocall/delete_member/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ 'name': NAME, 'room_name': CHANNEL, 'UID': UID })
    });
    let member = await response.json();
    var audioEl = document.getElementById("audio4");
    if (audioEl) audioEl.play();
    return member;
};

// Función para obtener CSRF token
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
    // Si no se encuentra en cookies, intentar obtener del meta tag
    if (!cookieValue) {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            cookieValue = metaTag.getAttribute('content');
        }
    }
    return cookieValue;
}

// Función para obtener el token CSRF de forma segura
function getCSRFToken() {
    const token = getCookie('csrftoken');
    if (!token || token.length < 10) {
        console.warn('Token CSRF no encontrado o inválido. Intentando obtener de meta tag...');
        // Intentar obtener del meta tag si existe
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        // Si aún no hay token, intentar obtener del input hidden si existe
        const csrfInput = document.querySelector('[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value;
        }
        console.error('No se pudo obtener el token CSRF');
        return null;
    }
    return token;
}

// Inicializar cuando el DOM esté listo
window.addEventListener("beforeunload", deleteMember);

// Función para conectar todos los botones
function connectControlButtons() {
    console.log('Conectando botones de control...');
    
    // Botón de salir
    const leaveBtn = document.getElementById('leave-btn');
    if (leaveBtn) {
        // Remover listeners anteriores si existen
        const newLeaveBtn = leaveBtn.cloneNode(true);
        leaveBtn.parentNode.replaceChild(newLeaveBtn, leaveBtn);
        newLeaveBtn.addEventListener('click', leaveAndRemoveLocalStream);
        console.log('Botón de salir conectado');
    } else {
        console.warn('Botón de salir no encontrado');
    }
    
    // Botón de cámara
    const cameraBtn = document.getElementById('camera-btn');
    if (cameraBtn) {
        const newCameraBtn = cameraBtn.cloneNode(true);
        cameraBtn.parentNode.replaceChild(newCameraBtn, cameraBtn);
        newCameraBtn.addEventListener('click', toggleCamera);
        console.log('Botón de cámara conectado');
    } else {
        console.warn('Botón de cámara no encontrado');
    }
    
    // Botón de micrófono
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        const newMicBtn = micBtn.cloneNode(true);
        micBtn.parentNode.replaceChild(newMicBtn, micBtn);
        newMicBtn.addEventListener('click', toggleMic);
        console.log('Botón de micrófono conectado');
    } else {
        console.warn('Botón de micrófono no encontrado');
    }
    
    // Botón de compartir pantalla
    const shareBtn = document.getElementById('share-btn') || document.getElementById('screen-share-btn');
    if (shareBtn) {
        const newShareBtn = shareBtn.cloneNode(true);
        shareBtn.parentNode.replaceChild(newShareBtn, shareBtn);
        newShareBtn.addEventListener('click', toggleShare);
        console.log('Botón de compartir pantalla conectado');
    } else {
        console.warn('Botón de compartir pantalla no encontrado');
    }
}

// Función para mutear/desmutear audio de un usuario remoto
function toggleRemoteMute(uid, buttonElement) {
    if (!remoteUsers[uid]) {
        console.error('Usuario remoto no encontrado:', uid);
        return;
    }
    
    const user = remoteUsers[uid];
    if (!user.audioTrack) {
        console.warn('Usuario no tiene track de audio:', uid);
        Swal.fire({
            icon: 'warning',
            title: 'Sin audio',
            text: 'Este usuario no tiene audio disponible',
            timer: 2000,
            showConfirmButton: false
        });
        return;
    }
    
    // Verificar si está muteado (usando setVolume o isPlaying)
    let isMuted = false;
    try {
        // Intentar obtener el estado del volumen
        const volume = user.audioTrack.getVolumeLevel ? user.audioTrack.getVolumeLevel() : null;
        isMuted = volume === 0 || (buttonElement && buttonElement.classList.contains('muted'));
    } catch (e) {
        // Si no se puede obtener el volumen, usar la clase del botón
        isMuted = buttonElement && buttonElement.classList.contains('muted');
    }
    
    if (isMuted) {
        // Desmutear: restaurar volumen y reproducir
        try {
            user.audioTrack.setVolume(100);
            if (user.audioTrack.play) {
                user.audioTrack.play();
            }
            buttonElement.classList.remove('muted');
            const icon = buttonElement.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-volume-mute');
                icon.classList.add('fa-volume-up');
            }
            buttonElement.title = 'Mutear audio';
            console.log('Audio desmuteado para usuario:', uid);
            
            Swal.fire({
                icon: 'success',
                title: 'Audio activado',
                text: 'El audio de este participante está activado',
                timer: 1500,
                showConfirmButton: false,
                toast: true,
                position: 'top-end'
            });
        } catch (error) {
            console.error('Error al desmutear:', error);
        }
    } else {
        // Mutear: establecer volumen a 0
        try {
            user.audioTrack.setVolume(0);
            buttonElement.classList.add('muted');
            const icon = buttonElement.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-volume-up');
                icon.classList.add('fa-volume-mute');
            }
            buttonElement.title = 'Desmutear audio';
            console.log('Audio muteado para usuario:', uid);
            
            Swal.fire({
                icon: 'info',
                title: 'Audio desactivado',
                text: 'El audio de este participante está desactivado',
                timer: 1500,
                showConfirmButton: false,
                toast: true,
                position: 'top-end'
            });
        } catch (error) {
            console.error('Error al mutear:', error);
        }
    }
}

// Actualizar window.AgoraVideoCall con la función de mute
if (window.AgoraVideoCall) {
    window.AgoraVideoCall.toggleRemoteMute = toggleRemoteMute;
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, inicializando...');
    
    // Inicializar datos de sesión
    initializeSessionData();
    
    // Conectar botones inmediatamente
    connectControlButtons();
    
    // NO llamar joinAndDisplayLocalStream aquí
    // Se llamará desde el template cuando todo esté listo
    // Esto previene múltiples llamadas
});

// También conectar cuando la página esté completamente cargada
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', connectControlButtons);
} else {
    // DOM ya está listo
    setTimeout(connectControlButtons, 100);
}

