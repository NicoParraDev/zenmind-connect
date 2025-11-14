"""
Vistas para el sistema de Chatbot con OpenAI.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Persona, ChatConversation, ChatMessageBot, Psicologo
from .chatbot import procesar_mensaje_chatbot, obtener_conversacion_activa, obtener_historial_mensajes
from .decorators import get_client_ip

logger = logging.getLogger(__name__)


@login_required
def chatbot_view(request: HttpRequest, conversacion_id: int = None) -> HttpResponse:
    """
    Vista principal del chatbot.
    Mantiene la conversación activa o carga una conversación específica.
    Solo crea nueva conversación si no hay ninguna activa.
    
    Args:
        request: HttpRequest
        conversacion_id: ID opcional de conversación a cargar
        
    Returns:
        HttpResponse: Renderiza la interfaz del chatbot
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        
        # Si se especifica un ID de conversación, cargar esa
        if conversacion_id:
            conversacion = get_object_or_404(
                ChatConversation, 
                id=conversacion_id, 
                persona=persona
            )
            # Marcar como activa
            ChatConversation.objects.filter(
                persona=persona,
                is_active=True
            ).update(is_active=False)
            conversacion.is_active = True
            conversacion.save()
        else:
            # Obtener conversación activa existente o crear una nueva
            from .chatbot import obtener_conversacion_activa
            conversacion = obtener_conversacion_activa(persona)
        
        # Obtener historial de mensajes de la conversación actual
        mensajes = ChatMessageBot.objects.filter(
            conversation=conversacion
        ).order_by('created_at')[:50]
        
        # Obtener todas las conversaciones del usuario (para el sidebar)
        conversaciones = ChatConversation.objects.filter(
            persona=persona
        ).order_by('-updated_at')[:20]  # Últimas 20 conversaciones
        
        # Agregar título a cada conversación (primer mensaje del usuario)
        conversaciones_con_titulo = []
        for conv in conversaciones:
            primer_mensaje = ChatMessageBot.objects.filter(
                conversation=conv,
                role='user'
            ).order_by('created_at').first()
            
            titulo = "Nueva conversación"
            if primer_mensaje:
                titulo = primer_mensaje.message[:50]
                if len(primer_mensaje.message) > 50:
                    titulo += "..."
            
            conversaciones_con_titulo.append({
                'conversacion': conv,
                'titulo': titulo
            })
        
        context = {
            'persona': persona,
            'conversacion': conversacion,
            'mensajes': mensajes,
            'conversaciones_con_titulo': conversaciones_con_titulo,
        }
        
        return render(request, 'core/chatbot.html', context)
        
    except Persona.DoesNotExist:
        messages.error(request, 'Debes tener un perfil para usar el chatbot.')
        return redirect('form_persona')
    except Exception as e:
        logger.error(f"Error en chatbot_view: {e}", exc_info=True)
        messages.error(request, 'Ocurrió un error al cargar el chatbot.')
        return redirect('index')


@login_required
@require_http_methods(["POST"])
def chatbot_send_message(request: HttpRequest) -> JsonResponse:
    """
    API endpoint para enviar un mensaje al chatbot.
    
    Args:
        request: HttpRequest con mensaje en POST
        
    Returns:
        JsonResponse con la respuesta del chatbot
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        
        mensaje = request.POST.get('mensaje', '').strip()
        
        if not mensaje:
            return JsonResponse({
                'error': 'El mensaje no puede estar vacío.'
            }, status=400)
        
        # Validar longitud
        if len(mensaje) > 1000:
            return JsonResponse({
                'error': 'El mensaje es demasiado largo (máximo 1000 caracteres).'
            }, status=400)
        
        # Procesar mensaje
        resultado = procesar_mensaje_chatbot(persona, mensaje)
        
        # Preparar respuesta
        respuesta_data = {
            'respuesta': resultado['respuesta'],
            'es_crisis': resultado['es_crisis'],
            'conversacion_id': resultado['conversacion_id'],
        }
        
        # Si hay psicólogo recomendado, agregar información
        if resultado['psicologo_recomendado']:
            psicologo = resultado['psicologo_recomendado']
            respuesta_data['psicologo'] = {
                'id': psicologo.id,
                'nombre': psicologo.nombre,
                'especialidad': psicologo.especialidad.nombre if psicologo.especialidad else '',
                'email': psicologo.email,
            }
        
        return JsonResponse(respuesta_data)
        
    except Persona.DoesNotExist:
        return JsonResponse({
            'error': 'Debes tener un perfil para usar el chatbot.'
        }, status=403)
    except Exception as e:
        logger.error(f"Error en chatbot_send_message: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Ocurrió un error al procesar tu mensaje. Por favor, intenta nuevamente.'
        }, status=500)


@login_required
def chatbot_get_history(request: HttpRequest, conversacion_id: int) -> JsonResponse:
    """
    Obtiene el historial de mensajes de una conversación.
    
    Args:
        request: HttpRequest
        conversacion_id: ID de la conversación
        
    Returns:
        JsonResponse con el historial
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        conversacion = get_object_or_404(ChatConversation, id=conversacion_id, persona=persona)
        
        mensajes = ChatMessageBot.objects.filter(
            conversation=conversacion
        ).order_by('created_at')
        
        mensajes_data = []
        for msg in mensajes:
            mensajes_data.append({
                'id': msg.id,
                'role': msg.role,
                'message': msg.message,
                'created_at': msg.created_at.isoformat(),
                'is_crisis': msg.is_crisis_detected,
                'psicologo_recomendado': {
                    'id': msg.psicologo_recomendado.id,
                    'nombre': msg.psicologo_recomendado.nombre,
                } if msg.psicologo_recomendado else None
            })
        
        return JsonResponse({
            'conversacion_id': conversacion.id,
            'mensajes': mensajes_data
        })
        
    except Exception as e:
        logger.error(f"Error en chatbot_get_history: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Error al obtener el historial.'
        }, status=500)


@login_required
def chatbot_new_conversation(request: HttpRequest) -> JsonResponse:
    """
    Crea una nueva conversación.
    
    Args:
        request: HttpRequest
        
    Returns:
        JsonResponse con el ID de la nueva conversación
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        
        # Desactivar conversaciones anteriores
        ChatConversation.objects.filter(
            persona=persona,
            is_active=True
        ).update(is_active=False)
        
        # Crear nueva conversación
        from .chatbot import obtener_conversacion_activa
        conversacion = obtener_conversacion_activa(persona)
        
        return JsonResponse({
            'conversacion_id': conversacion.id,
            'success': True,
            'redirect_url': f'/chatbot/{conversacion.id}/'
        })
        
    except Exception as e:
        logger.error(f"Error en chatbot_new_conversation: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Error al crear nueva conversación.'
        }, status=500)


@login_required
def chatbot_list_conversations(request: HttpRequest) -> JsonResponse:
    """
    Obtiene la lista de conversaciones del usuario.
    
    Args:
        request: HttpRequest
        
    Returns:
        JsonResponse con la lista de conversaciones
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        
        conversaciones = ChatConversation.objects.filter(
            persona=persona
        ).order_by('-updated_at')[:50]
        
        conversaciones_data = []
        for conv in conversaciones:
            # Obtener el primer mensaje del usuario como título
            primer_mensaje = ChatMessageBot.objects.filter(
                conversation=conv,
                role='user'
            ).order_by('created_at').first()
            
            titulo = "Nueva conversación"
            if primer_mensaje:
                titulo = primer_mensaje.message[:50]
                if len(primer_mensaje.message) > 50:
                    titulo += "..."
            
            conversaciones_data.append({
                'id': conv.id,
                'titulo': titulo,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'is_active': conv.is_active,
                'message_count': conv.get_message_count(),
            })
        
        return JsonResponse({
            'conversaciones': conversaciones_data
        })
        
    except Exception as e:
        logger.error(f"Error en chatbot_list_conversations: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Error al obtener conversaciones.'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def chatbot_delete_conversation(request: HttpRequest, conversacion_id: int) -> JsonResponse:
    """
    Elimina una conversación del usuario.
    
    Args:
        request: HttpRequest
        conversacion_id: ID de la conversación a eliminar
        
    Returns:
        JsonResponse con el resultado
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        conversacion = get_object_or_404(
            ChatConversation, 
            id=conversacion_id, 
            persona=persona
        )
        
        # Eliminar la conversación (esto también eliminará todos los mensajes por CASCADE)
        conversacion.delete()
        
        logger.info(f"Conversación {conversacion_id} eliminada por {persona}")
        
        return JsonResponse({
            'success': True,
            'message': 'Conversación eliminada correctamente'
        })
        
    except ChatConversation.DoesNotExist:
        return JsonResponse({
            'error': 'Conversación no encontrada.'
        }, status=404)
    except Exception as e:
        logger.error(f"Error en chatbot_delete_conversation: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Error al eliminar la conversación.'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def chatbot_delete_multiple(request: HttpRequest) -> JsonResponse:
    """
    Elimina múltiples conversaciones del usuario.
    
    Args:
        request: HttpRequest con JSON body: {"ids": [1, 2, 3, ...]}
        
    Returns:
        JsonResponse con el resultado
    """
    try:
        import json
        persona = get_object_or_404(Persona, user=request.user)
        
        # Obtener los IDs del body JSON
        data = json.loads(request.body)
        ids = data.get('ids', [])
        
        if not ids or not isinstance(ids, list):
            return JsonResponse({
                'error': 'Se requiere una lista de IDs válidos.'
            }, status=400)
        
        # Validar que todas las conversaciones pertenezcan al usuario
        conversaciones = ChatConversation.objects.filter(
            id__in=ids,
            persona=persona
        )
        
        # Verificar que se encontraron todas las conversaciones solicitadas
        found_ids = set(conversaciones.values_list('id', flat=True))
        requested_ids = set(ids)
        
        if found_ids != requested_ids:
            missing_ids = requested_ids - found_ids
            return JsonResponse({
                'error': f'No se encontraron algunas conversaciones: {list(missing_ids)}'
            }, status=404)
        
        # Eliminar las conversaciones (esto también eliminará todos los mensajes por CASCADE)
        count = conversaciones.count()
        conversaciones.delete()
        
        logger.info(f"{count} conversación(es) eliminada(s) por {persona}: {ids}")
        
        return JsonResponse({
            'success': True,
            'message': f'{count} conversación(es) eliminada(s) correctamente',
            'count': count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Formato JSON inválido.'
        }, status=400)
    except Exception as e:
        logger.error(f"Error en chatbot_delete_multiple: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Error al eliminar las conversaciones.'
        }, status=500)

