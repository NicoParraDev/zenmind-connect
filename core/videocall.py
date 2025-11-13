"""
Vistas para sistema de videollamadas y chat integrado.
"""
import json
import random
import time
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from decouple import config
from .models import Persona, VideoCallRoom, RoomMember, ChatMessage, Agenda, HorarioAgenda
from .decorators import rate_limit

logger = logging.getLogger(__name__)

try:
    from agora_token_builder import RtcTokenBuilder
    AGORA_AVAILABLE = True
except ImportError:
    AGORA_AVAILABLE = False
    logger.warning("agora-token-builder no está instalado. Instalar con: pip install agora-token-builder")


# ============================================
# VISTAS DE VIDEOCALL
# ============================================

def get_user_allowed_roles(persona):
    """
    Determina qué roles puede seleccionar un usuario según su tipo de usuario.
    Retorna una lista de roles permitidos.
    
    Lógica basada en los tipos de usuario reales en la BD:
    - "Psicologo" -> puede ser psicologo
    - "Usuario", "Regular", "Usuario Normal" -> solo paciente (usuario normal)
    - Todos pueden ser "audience" en eventos grupales
    """
    allowed_roles = ['paciente']  # Todos pueden ser pacientes
    
    try:
        # Obtener el tipo de usuario de forma segura
        if persona and hasattr(persona, 'tipousuario') and persona.tipousuario:
            if hasattr(persona.tipousuario, 'tipoUsuario'):
                tipo_usuario = persona.tipousuario.tipoUsuario or ''
            else:
                tipo_usuario = ''
        else:
            tipo_usuario = ''
        
        tipo_usuario_lower = tipo_usuario.lower() if tipo_usuario else ''
        
        # Verificar si es psicólogo (tipo exacto "Psicologo" en la BD)
        if tipo_usuario == 'Psicologo' or 'psicologo' in tipo_usuario_lower:
            allowed_roles.append('psicologo')
        
        # Verificar si es practicante (si existe este tipo en la BD)
        if 'practicante' in tipo_usuario_lower or 'estudiante' in tipo_usuario_lower or 'pasant' in tipo_usuario_lower:
            allowed_roles.append('practicante')
    except (AttributeError, Exception) as e:
        # Si hay algún error, solo permitir roles básicos
        logger.warning(f"Error obteniendo tipo de usuario para {persona}: {e}")
    
    # En eventos grupales, todos pueden ser audiencia
    allowed_roles.append('audience')
    
    return list(set(allowed_roles))  # Eliminar duplicados


@login_required
def videocall_lobby(request):
    """
    Página de entrada para crear/entrar a una sala de videollamada.
    """
    try:
        persona = Persona.objects.get(user=request.user)
    except Persona.DoesNotExist:
        messages.error(request, 'Debes completar tu perfil primero.')
        return redirect('form_persona')
    
    # Determinar roles permitidos para este usuario
    allowed_roles = get_user_allowed_roles(persona)
    
    return render(request, 'core/videocall_lobby.html', {
        'persona': persona,
        'allowed_roles': allowed_roles,
        'is_psicologo': 'psicologo' in allowed_roles,
        'is_practicante': 'practicante' in allowed_roles,
    })


@login_required
def videocall_room(request, room_name):
    """
    Vista unificada de sala de videollamada con chat integrado.
    """
    try:
        persona = Persona.objects.get(user=request.user)
    except Persona.DoesNotExist:
        messages.error(request, 'Debes completar tu perfil primero.')
        return redirect('form_persona')
    
    # Obtener o crear sala
    # Si viene desde el lobby, obtener tipo de sala del request
    room_type = request.GET.get('room_type', 'private')
    is_couple_therapy = request.GET.get('is_couple_therapy', 'false').lower() == 'true'
    
    # Calcular máximo de participantes según tipo
    if room_type == 'group':
        max_participants = 50
    elif is_couple_therapy:
        max_participants = 5  # Psicólogo + Practicante + Pareja (2 personas)
    else:
        max_participants = 3  # Psicólogo + Practicante + Paciente
    
    room, created = VideoCallRoom.objects.get_or_create(
        name=room_name,
        defaults={
            'created_by': persona,
            'is_active': True,
            'room_type': room_type,
            'is_couple_therapy': is_couple_therapy,
            'max_participants': max_participants
        }
    )
    
    # Si la sala ya existe pero no tiene tipo, actualizarlo
    if not created:
        if not room.room_type:
            room.room_type = room_type
        if room_type == 'private':
            room.is_couple_therapy = is_couple_therapy
            room.max_participants = max_participants
        elif room_type == 'group':
            room.max_participants = 50
        room.save()
    
    if not room.is_active:
        messages.error(request, 'Esta sala no está disponible.')
        return redirect('videocall_lobby')
    
    # Obtener mensajes del chat (últimos 50)
    messages_list = ChatMessage.objects.filter(room=room).order_by('created_at')[:50]
    
    # Obtener miembros activos
    members = RoomMember.objects.filter(room=room, insession=True)
    
    # Determinar rol del usuario actual si no está en la lista de miembros
    user_role = 'paciente'  # Por defecto
    if room.room_type == 'group':
        # En eventos grupales, todos son audiencia por defecto (excepto el creador y practicantes)
        if room.created_by == persona:
            user_role = 'psicologo'
        else:
            # Buscar si el usuario ya es miembro (puede ser practicante)
            user_member = members.filter(persona=persona).first()
            if user_member and user_member.role == 'practicante':
                user_role = 'practicante'
            else:
                user_role = 'audience'
    else:
        # Buscar si el usuario ya es miembro
        user_member = members.filter(persona=persona).first()
        if user_member:
            user_role = user_member.role
        else:
            user_role = 'paciente'
    
    return render(request, 'core/videocall_room.html', {
        'room': room,
        'messages': messages_list,
        'members': members,
        'persona': persona,
        'user': request.user,
        'user_role': user_role,
    })


@login_required
@require_http_methods(["GET"])
def get_agora_token(request):
    """
    Genera token de Agora para autenticación en videollamada.
    """
    if not AGORA_AVAILABLE:
        return JsonResponse({'error': 'Agora SDK no disponible'}, status=500)
    
    # Obtener credenciales de variables de entorno
    app_id = config('AGORA_APP_ID', default='')
    app_certificate = config('AGORA_APP_CERTIFICATE', default='')
    
    # Validar que las credenciales existan y no sean placeholders
    if not app_id or not app_certificate:
        logger.error("Credenciales de Agora no configuradas en .env")
        return JsonResponse({
            'error': 'Configuración de Agora no disponible. Por favor, configura AGORA_APP_ID y AGORA_APP_CERTIFICATE en tu archivo .env.'
        }, status=500)
    
    if app_id == 'your-agora-app-id' or app_certificate == 'your-agora-app-certificate':
        logger.error("Credenciales de Agora son placeholders en .env")
        return JsonResponse({
            'error': 'Configuración de Agora no disponible. Por favor, reemplaza los valores placeholder en tu archivo .env con tus credenciales reales de Agora.'
        }, status=500)
    
    channel_name = request.GET.get('channel', '')
    if not channel_name:
        return JsonResponse({'error': 'Channel name requerido'}, status=400)
    
    try:
        # Generar UID aleatorio
        uid = random.randint(1, 230)
        
        # Configurar token
        expiration_time = 3600  # 1 hora
        current_timestamp = int(time.time())
        privilege_expired_ts = current_timestamp + expiration_time
        role = 1  # Publisher
        
        # Generar token
        token = RtcTokenBuilder.buildTokenWithUid(
            app_id, 
            app_certificate, 
            channel_name, 
            uid, 
            role, 
            privilege_expired_ts
        )
        
        logger.info(f"Token generado para usuario {request.user.username} en canal {channel_name}")
        
        return JsonResponse({
            'token': token, 
            'uid': uid,
            'app_id': app_id
        }, safe=False)
        
    except Exception as e:
        logger.error(f"Error generando token Agora: {e}", exc_info=True)
        error_message = f'Error generando token: {str(e)}'
        if 'certificate' in str(e).lower() or 'app_id' in str(e).lower():
            error_message += '. Verifica que las credenciales de Agora estén correctamente configuradas en el archivo .env'
        return JsonResponse({'error': error_message}, status=500)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def create_room(request):
    """
    Crea una sala con tipo y configuración.
    """
    try:
        persona = Persona.objects.get(user=request.user)
    except Persona.DoesNotExist:
        return JsonResponse({'error': 'Perfil no encontrado'}, status=400)
    
    try:
        data = json.loads(request.body)
        room_name = data.get('room_name')
        room_type = data.get('room_type', 'private')
        is_couple_therapy = data.get('is_couple_therapy', False)
        
        if not room_name:
            return JsonResponse({'error': 'Nombre de sala requerido'}, status=400)
        
        # Calcular máximo de participantes según tipo
        if room_type == 'group':
            max_participants = 50
        elif is_couple_therapy:
            max_participants = 5  # Psicólogo + Practicante + Pareja (2 personas)
        else:
            max_participants = 3  # Psicólogo + Practicante + Paciente
        
        room, created = VideoCallRoom.objects.get_or_create(
            name=room_name,
            defaults={
                'created_by': persona,
                'is_active': True,
                'room_type': room_type,
                'is_couple_therapy': is_couple_therapy if room_type == 'private' else False,
                'max_participants': max_participants
            }
        )
        
        if not created:
            # Actualizar tipo si no estaba configurado
            if not room.room_type:
                room.room_type = room_type
                if room_type == 'private':
                    room.is_couple_therapy = is_couple_therapy
                    room.max_participants = max_participants
                else:
                    room.max_participants = 50
                room.save()
        
        return JsonResponse({
            'success': True,
            'room_name': room.name,
            'room_type': room.room_type,
            'created': created
        }, safe=False)
        
    except Exception as e:
        logger.error(f"Error creando sala: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def create_room_member(request):
    """
    Crea o obtiene un miembro en una sala de videollamada.
    """
    try:
        persona = Persona.objects.get(user=request.user)
    except Persona.DoesNotExist:
        return JsonResponse({'error': 'Perfil no encontrado'}, status=400)
    
    try:
        data = json.loads(request.body)
        room_name = data.get('room_name')
        uid = data.get('UID')
        user_role = data.get('user_role')
        
        if not room_name or not uid:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        # Obtener sala
        try:
            room = VideoCallRoom.objects.get(name=room_name, is_active=True)
        except VideoCallRoom.DoesNotExist:
            return JsonResponse({'error': f'Sala "{room_name}" no encontrada o inactiva'}, status=404)
        
        # Validar que el usuario tenga permiso para el rol seleccionado
        allowed_roles = get_user_allowed_roles(persona)
        if user_role and user_role not in allowed_roles:
            # Si el usuario intenta usar un rol no permitido, usar el por defecto
            logger.warning(f"Usuario {persona} intentó usar rol {user_role} no permitido. Roles permitidos: {allowed_roles}")
            user_role = None
        
        # Determinar rol por defecto según tipo de sala y tipo de usuario
        if not user_role:
            if room.room_type == 'group':
                # En eventos grupales, todos son audiencia por defecto (excepto el creador y practicantes)
                if room.created_by == persona:
                    user_role = 'psicologo' if 'psicologo' in allowed_roles else 'audience'
                elif 'practicante' in allowed_roles:
                    # Si es practicante, puede mantener su rol
                    user_role = 'practicante'
                else:
                    user_role = 'audience'
            else:
                # En sesiones privadas, por defecto es paciente
                # (El psicólogo y practicante deben seleccionar su rol explícitamente)
                user_role = 'paciente'
        
        # Verificar límite de participantes
        active_members = room.members.filter(insession=True).count()
        if active_members >= room.max_participants:
            return JsonResponse({'error': 'Sala llena'}, status=403)
        
        # Crear o obtener miembro
        member, created = RoomMember.objects.get_or_create(
            room=room,
            uid=uid,
            defaults={
                'persona': persona,
                'role': user_role,
                'insession': True
            }
        )
        
        if not created:
            # Si ya existe, actualizar
            member.insession = True
            # Actualizar rol si cambió o si no tenía rol asignado
            if user_role and (not member.role or member.role != user_role):
                member.role = user_role
            member.save()
        
        logger.info(f"Miembro {persona} creado/actualizado en sala {room_name} con rol {user_role}")
        
        # Obtener nombre de forma segura
        nombre = getattr(persona, 'nombre', '') or ''
        apellido = getattr(persona, 'apellido', '') or ''
        nombre_completo = f"{nombre} {apellido}".strip() or str(persona)
        
        return JsonResponse({
            'name': nombre_completo,
            'role': member.role,
            'created': created
        }, safe=False)
        
    except Exception as e:
        logger.error(f"Error creando miembro: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        # Devolver un mensaje de error más descriptivo
        error_message = str(e)
        if isinstance(e, AttributeError):
            error_message = f"Error de atributo: {error_message}. Verifica que el perfil del usuario esté completo."
        return JsonResponse({
            'error': error_message,
            'error_type': type(e).__name__
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_room_member(request):
    """
    Obtiene información de un miembro en una sala.
    Si el UID corresponde al usuario actual, verifica si sigue siendo miembro activo.
    Si el UID corresponde a otro usuario, solo verifica que exista en la sala.
    """
    try:
        uid = request.GET.get('UID')
        room_name = request.GET.get('room_name')
        
        if not uid or not room_name:
            return JsonResponse({'error': 'Parámetros incompletos', 'is_active': False}, status=400)
        
        room = get_object_or_404(VideoCallRoom, name=room_name)
        
        try:
            persona = Persona.objects.get(user=request.user)
        except Persona.DoesNotExist:
            return JsonResponse({'error': 'Perfil no encontrado', 'is_active': False}, status=400)
        
        # IMPORTANTE: Verificar SOLO por UID, NO por persona
        # Esto evita problemas cuando múltiples navegadores comparten la misma sesión
        # El UID es único por navegador/sesión de Agora, así que es la forma más precisa
        
        # Buscar el miembro SOLO por UID (ignorar persona completamente)
        try:
            # Primero intentar con insession=True (miembro activo)
            member = RoomMember.objects.get(room=room, uid=str(uid), insession=True)
            return JsonResponse({
                'name': f"{member.persona.nombre} {member.persona.apellido}",
                'is_active': True
            }, safe=False)
        except RoomMember.DoesNotExist:
            # Si no está activo, buscar sin restricción de insession
            try:
                member = RoomMember.objects.get(room=room, uid=str(uid))
                # Si existe pero insession=False, fue expulsado o salió
                return JsonResponse({
                    'name': f"{member.persona.nombre} {member.persona.apellido}",
                    'is_active': member.insession  # False si fue expulsado
                }, safe=False)
            except RoomMember.DoesNotExist:
                # El miembro con este UID no existe en la sala
                # Esto puede ocurrir si:
                # 1. El usuario se unió a Agora pero aún no se creó su registro en BD
                # 2. El UID es incorrecto
                # En este caso, NO devolver is_active=False porque causaría expulsión incorrecta
                # En su lugar, devolver is_active=True para permitir que el usuario continúe
                logger.info(f"Miembro con UID {uid} no encontrado en sala {room_name} - permitiendo continuar (puede estar en proceso de unirse)")
                return JsonResponse({
                    'name': f"Usuario {uid}",
                    'is_active': True  # Permitir que continúe si no existe registro aún
                }, safe=False)
        except Exception as e:
            logger.error(f"Error buscando miembro con UID {uid}: {e}", exc_info=True)
            # En caso de error, devolver nombre genérico
            return JsonResponse({
                'name': f"Usuario {uid}",
                'is_active': False
            }, safe=False)
        
    except Exception as e:
        logger.error(f"Error obteniendo miembro: {e}", exc_info=True)
        # En caso de error general, devolver nombre genérico en lugar de error 500
        return JsonResponse({
            'name': f"Usuario {uid if uid else 'desconocido'}",
            'is_active': False
        }, safe=False)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def delete_room_member(request):
    """
    Elimina un miembro de una sala (cuando sale).
    """
    try:
        persona = Persona.objects.get(user=request.user)
    except Persona.DoesNotExist:
        return JsonResponse({'error': 'Perfil no encontrado'}, status=400)
    
    try:
        data = json.loads(request.body)
        room_name = data.get('room_name')
        uid = data.get('UID')
        
        if not room_name or not uid:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        room = get_object_or_404(VideoCallRoom, name=room_name)
        member = get_object_or_404(RoomMember, room=room, uid=uid, persona=persona)
        
        # Marcar como fuera de sesión
        member.leave_session()
        
        logger.info(f"Miembro {persona} salió de sala {room_name}")
        
        return JsonResponse({'success': True, 'message': 'Member deleted'}, safe=False)
        
    except Exception as e:
        logger.error(f"Error eliminando miembro: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# VISTAS DE CHAT
# ============================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
@rate_limit(max_attempts=30, window=60, key_prefix='chat_send')
def send_chat_message(request):
    """
    Envía un mensaje de chat en una sala de videollamada.
    """
    try:
        persona = Persona.objects.get(user=request.user)
    except Persona.DoesNotExist:
        return JsonResponse({'error': 'Perfil no encontrado'}, status=400)
    
    try:
        data = json.loads(request.body)
        room_name = data.get('room_name', '').strip()
        message_text = data.get('message', '').strip()
        
        # Validaciones
        if not room_name:
            return JsonResponse({'error': 'Nombre de sala requerido'}, status=400)
        
        if not message_text:
            return JsonResponse({'error': 'Mensaje no puede estar vacío'}, status=400)
        
        if len(message_text) > 5000:
            return JsonResponse({'error': 'Mensaje muy largo (máximo 5000 caracteres)'}, status=400)
        
        # Obtener sala
        try:
            room = VideoCallRoom.objects.get(name=room_name, is_active=True)
        except VideoCallRoom.DoesNotExist:
            return JsonResponse({'error': 'Sala no encontrada o inactiva'}, status=404)
        
        # Crear mensaje
        try:
            message = ChatMessage.objects.create(
                room=room,
                author=persona,
                message=message_text
            )
            
            # Log para debugging de pizarra
            is_whiteboard = message_text.startswith('WHITEBOARD:')
            if is_whiteboard:
                logger.info(f"[send_chat_message] ✅ Mensaje de PIZARRA guardado: ID={message.id}, Autor={persona}, Longitud={len(message_text)}")
            else:
                logger.info(f"Mensaje enviado por {persona} en sala {room_name}")
        except Exception as create_error:
            logger.error(f"Error creando mensaje: {create_error}", exc_info=True)
            return JsonResponse({'error': f'Error al crear mensaje: {str(create_error)}'}, status=500)
        
        # Obtener nombre del autor de forma segura
        try:
            author_name = message.get_author_name()
        except Exception as name_error:
            logger.warning(f"Error obteniendo nombre del autor: {name_error}")
            author_name = f"{persona.nombre} {persona.apellido}" if hasattr(persona, 'nombre') and hasattr(persona, 'apellido') else str(persona)
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'author': author_name,
            'message': message.message,
            'created_at': message.created_at.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return JsonResponse({'error': f'Error del servidor: {str(e)}'}, status=500)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def set_typing_status(request):
    """
    Establece el estado de escritura del usuario en una sala.
    """
    try:
        persona = Persona.objects.get(user=request.user)
    except Persona.DoesNotExist:
        return JsonResponse({'error': 'Perfil no encontrado'}, status=400)
    
    try:
        data = json.loads(request.body)
        room_name = data.get('room_name', '').strip()
        is_typing = data.get('is_typing', False)
        
        if not room_name:
            return JsonResponse({'error': 'Nombre de sala requerido'}, status=400)
        
        try:
            room = VideoCallRoom.objects.get(name=room_name, is_active=True)
        except VideoCallRoom.DoesNotExist:
            return JsonResponse({'error': 'Sala no encontrada o inactiva'}, status=404)
        
        # Usar cache para almacenar el estado de escritura (expira en 5 segundos)
        from django.core.cache import cache
        cache_key = f'typing_{room_name}_{persona.pk}'
        
        if is_typing:
            # Guardar nombre del usuario escribiendo por 5 segundos
            try:
                author_name = f"{persona.nombre} {persona.apellido}" if hasattr(persona, 'nombre') and hasattr(persona, 'apellido') else str(persona)
            except:
                author_name = str(persona)
            cache.set(cache_key, author_name, 5)
            logger.debug(f"Usuario {author_name} está escribiendo en sala {room_name}")
        else:
            cache.delete(cache_key)
            logger.debug(f"Usuario {persona.pk} dejó de escribir en sala {room_name}")
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Error estableciendo estado de escritura: {e}", exc_info=True)
        return JsonResponse({'error': f'Error del servidor: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_typing_status(request, room_name):
    """
    Obtiene quién está escribiendo en una sala.
    """
    try:
        room = VideoCallRoom.objects.get(name=room_name, is_active=True)
    except VideoCallRoom.DoesNotExist:
        return JsonResponse({'error': 'Sala no encontrada o inactiva'}, status=404)
    
    try:
        from django.core.cache import cache
        from .models import Persona
        
        # Obtener todos los usuarios que están escribiendo
        typing_users = []
        current_persona = None
        try:
            current_persona = Persona.objects.get(user=request.user)
        except Persona.DoesNotExist:
            pass
        
        # Buscar en todos los miembros activos de la sala (usar insession en lugar de is_active)
        room_members = RoomMember.objects.filter(room=room, insession=True)
        
        for member in room_members:
            # No incluir al usuario actual (comparar por pk o rut)
            if current_persona and member.persona.pk == current_persona.pk:
                continue
                
            cache_key = f'typing_{room_name}_{member.persona.pk}'
            typing_name = cache.get(cache_key)
            if typing_name:
                typing_users.append(typing_name)
        
        logger.debug(f"Usuarios escribiendo en sala {room_name}: {typing_users}")
        
        return JsonResponse({
            'typing_users': typing_users,
            'is_typing': len(typing_users) > 0
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de escritura: {e}", exc_info=True)
        return JsonResponse({'error': f'Error del servidor: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_chat_messages(request, room_name):
    """
    Obtiene los mensajes de chat de una sala.
    """
    try:
        try:
            room = VideoCallRoom.objects.get(name=room_name, is_active=True)
        except VideoCallRoom.DoesNotExist:
            return JsonResponse({'error': 'Sala no encontrada o inactiva'}, status=404)
        
        # Obtener mensajes (últimos 100, más recientes primero)
        messages = ChatMessage.objects.filter(room=room).order_by('-created_at')[:100]
        
        # Log para debugging con detalles de borrado
        whiteboard_count = sum(1 for msg in messages if msg.message and msg.message.startswith('WHITEBOARD:'))
        eraser_count = 0
        clear_count = 0
        for msg in messages:
            if msg.message and msg.message.startswith('WHITEBOARD:'):
                try:
                    action_str = msg.message.replace('WHITEBOARD:', '')
                    action = json.loads(action_str)
                    if action.get('tool') == 'eraser':
                        eraser_count += 1
                    elif action.get('type') == 'clear':
                        clear_count += 1
                except:
                    pass
        logger.info(f"[get_chat_messages] Sala {room_name}: {len(messages)} mensajes totales, {whiteboard_count} de pizarra (🧹 {eraser_count} borrados, 🗑️ {clear_count} limpiezas)")
        
        messages_data = []
        for msg in messages:
            try:
                author_name = msg.get_author_name()
            except Exception as name_error:
                logger.warning(f"Error obteniendo nombre del autor del mensaje {msg.id}: {name_error}")
                # Intentar obtener nombre directamente del autor
                if hasattr(msg, 'author') and msg.author:
                    if hasattr(msg.author, 'nombre') and hasattr(msg.author, 'apellido'):
                        author_name = f"{msg.author.nombre} {msg.author.apellido}"
                    else:
                        author_name = str(msg.author)
                else:
                    author_name = "Usuario desconocido"
            
            messages_data.append({
                'id': msg.id,
                'author': author_name,
                'message': msg.message,
                'created_at': msg.created_at.isoformat()
            })
        
        return JsonResponse({
            'messages': messages_data,
            'room_name': room_name
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo mensajes: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return JsonResponse({'error': f'Error del servidor: {str(e)}'}, status=500)


# ============================================
# VISTA PARA CREAR SALA DESDE RESERVA
# ============================================

@login_required
def crear_sala_desde_cita(request, horario_agenda_id):
    """
    Crea o accede a una sala de videollamada desde una cita confirmada.
    Permite tanto al psicólogo como al paciente acceder a la misma sala.
    """
    try:
        persona = Persona.objects.get(user=request.user)
    except Persona.DoesNotExist:
        messages.error(request, 'Debes completar tu perfil primero.')
        return redirect('form_persona')
    
    try:
        # Buscar el horario de agenda
        # El paciente tiene la reserva, pero el psicólogo también puede acceder
        horario_agenda = get_object_or_404(HorarioAgenda, id=horario_agenda_id)
        agenda = horario_agenda.agenda
        
        # Verificar que el usuario tenga acceso a esta cita
        # Puede ser el paciente (reservado_por) o cualquier usuario si la cita está reservada
        tiene_acceso = False
        if horario_agenda.reservado_por == persona:
            tiene_acceso = True  # Es el paciente que hizo la reserva
        elif horario_agenda.reservado_por:
            # Si hay una reserva, permitir acceso (el psicólogo puede crear/acceder a salas de sus citas)
            # También otros usuarios autorizados pueden acceder
            tiene_acceso = True
        else:
            # Si no hay reserva, solo el creador de la agenda puede acceder
            # Por ahora, permitimos acceso si no hay restricciones
            tiene_acceso = True
        
        if not tiene_acceso:
            messages.error(request, 'No tienes acceso a esta cita.')
            try:
                return redirect('area_de_persona', id=persona.rut)
            except:
                return redirect('index')
        
        # Buscar si ya existe una sala activa para esta agenda/horario
        # Usamos el horario_agenda.id como parte del nombre para identificar la sala
        existing_rooms = VideoCallRoom.objects.filter(
            agenda=agenda,
            is_active=True
        ).order_by('-created_at')
        
        # Buscar sala que coincida con este horario específico
        room = None
        for existing_room in existing_rooms:
            # El nombre de sala incluye el horario_agenda.id
            if str(horario_agenda_id) in existing_room.name:
                room = existing_room
                break
        
        # Si no existe, crear una nueva
        if not room:
            # Generar nombre único de sala basado en la cita
            room_name = f"CONSULTA-{agenda.psicologo.id}-{horario_agenda.id}"
            
            # Crear sala
            room = VideoCallRoom.objects.create(
                name=room_name,
                created_by=persona,
                agenda=agenda,
                is_active=True,
                room_type='private',  # Las citas son siempre privadas
                max_participants=3  # Psicólogo + Practicante + Paciente
            )
            
            logger.info(f"Sala creada desde cita: {room_name} por {persona}")
        else:
            logger.info(f"Accediendo a sala existente: {room.name} por {persona}")
        
        # Redirigir a la sala
        return redirect('videocall_room', room_name=room.name)
        
    except Exception as e:
        logger.error(f"Error creando/accediendo a sala desde cita: {e}", exc_info=True)
        messages.error(request, 'Error al acceder a la sala de videollamada.')
        try:
            return redirect('area_de_persona', id=persona.rut)
        except:
            return redirect('index')


@login_required
@require_http_methods(["GET"])
def get_room_participants(request, room_name):
    """
    Obtiene la lista de participantes activos en una sala.
    """
    try:
        try:
            room = VideoCallRoom.objects.get(name=room_name, is_active=True)
        except VideoCallRoom.DoesNotExist:
            return JsonResponse({'error': 'Sala no encontrada o inactiva'}, status=404)
        
        # Obtener usuario actual
        try:
            current_persona = Persona.objects.get(user=request.user)
        except Persona.DoesNotExist:
            return JsonResponse({'error': 'Perfil no encontrado'}, status=400)
        
        # Obtener miembros activos
        members = RoomMember.objects.filter(room=room, insession=True).select_related('persona')
        
        participants_data = []
        is_creator = room.created_by == current_persona
        is_psicologo = False
        
        # Verificar si el usuario actual es psicólogo
        try:
            if hasattr(current_persona, 'tipousuario') and current_persona.tipousuario:
                if hasattr(current_persona.tipousuario, 'tipoUsuario'):
                    tipo_usuario = current_persona.tipousuario.tipoUsuario or ''
                    is_psicologo = tipo_usuario == 'Psicologo' or 'psicologo' in tipo_usuario.lower()
        except:
            pass
        
        # Verificar si el usuario actual es superusuario
        is_admin = request.user.is_superuser
        
        # Determinar si puede expulsar usuarios (solo creador, psicólogo o admin)
        can_kick = is_creator or is_psicologo or is_admin
        
        for member in members:
            try:
                member_name = f"{member.persona.nombre} {member.persona.apellido}" if hasattr(member.persona, 'nombre') and hasattr(member.persona, 'apellido') else str(member.persona)
            except:
                member_name = str(member.persona)
            
            is_current_user = member.persona.pk == current_persona.pk
            
            participants_data.append({
                'id': member.id,
                'persona_id': member.persona.pk,
                'name': member_name,
                'role': member.role,
                'joined_at': member.joined_at.isoformat(),
                'is_current_user': is_current_user,
                'uid': member.uid
            })
        
        return JsonResponse({
            'participants': participants_data,
            'can_kick': can_kick,
            'total': len(participants_data)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo participantes: {e}", exc_info=True)
        return JsonResponse({'error': f'Error del servidor: {str(e)}'}, status=500)


@login_required
@csrf_protect
@require_http_methods(["POST"])
@rate_limit(max_attempts=10, window=60, key_prefix='kick_user')
def kick_participant(request):
    """
    Expulsa a un participante de la sala (solo para creador, psicólogo o admin).
    """
    try:
        persona = Persona.objects.get(user=request.user)
    except Persona.DoesNotExist:
        return JsonResponse({'error': 'Perfil no encontrado'}, status=400)
    
    try:
        data = json.loads(request.body)
        room_name = data.get('room_name', '').strip()
        participant_id = data.get('participant_id')
        
        if not room_name:
            return JsonResponse({'error': 'Nombre de sala requerido'}, status=400)
        
        if not participant_id:
            return JsonResponse({'error': 'ID de participante requerido'}, status=400)
        
        try:
            room = VideoCallRoom.objects.get(name=room_name, is_active=True)
        except VideoCallRoom.DoesNotExist:
            return JsonResponse({'error': 'Sala no encontrada o inactiva'}, status=404)
        
        # Verificar permisos
        is_creator = room.created_by == persona
        is_psicologo = False
        try:
            if hasattr(persona, 'tipousuario') and persona.tipousuario:
                if hasattr(persona.tipousuario, 'tipoUsuario'):
                    tipo_usuario = persona.tipousuario.tipoUsuario or ''
                    is_psicologo = tipo_usuario == 'Psicologo' or 'psicologo' in tipo_usuario.lower()
        except:
            pass
        
        is_admin = request.user.is_superuser
        
        if not (is_creator or is_psicologo or is_admin):
            return JsonResponse({'error': 'No tienes permisos para expulsar usuarios'}, status=403)
        
        # Obtener el miembro a expulsar
        try:
            member = RoomMember.objects.get(id=participant_id, room=room, insession=True)
        except RoomMember.DoesNotExist:
            return JsonResponse({'error': 'Participante no encontrado'}, status=404)
        
        # No permitir auto-expulsión
        if member.persona.pk == persona.pk:
            return JsonResponse({'error': 'No puedes expulsarte a ti mismo'}, status=400)
        
        # Guardar el UID de Agora antes de marcar como fuera de sesión
        agora_uid = member.uid
        
        # Marcar como fuera de sesión
        member.leave_session()
        
        logger.info(f"Usuario {member.persona} (UID: {agora_uid}) expulsado de sala {room_name} por {persona}")
        
        return JsonResponse({
            'success': True,
            'message': f'{member.persona.nombre} {member.persona.apellido} ha sido expulsado de la sala',
            'uid': agora_uid  # UID de Agora para remover el video
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Error expulsando participante: {e}", exc_info=True)
        return JsonResponse({'error': f'Error del servidor: {str(e)}'}, status=500)

