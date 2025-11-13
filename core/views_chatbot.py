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
def chatbot_view(request: HttpRequest) -> HttpResponse:
    """
    Vista principal del chatbot.
    
    Args:
        request: HttpRequest
        
    Returns:
        HttpResponse: Renderiza la interfaz del chatbot
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        
        # Obtener conversación activa
        from .chatbot import obtener_conversacion_activa
        conversacion = obtener_conversacion_activa(persona)
        
        # Obtener historial de mensajes
        mensajes = ChatMessageBot.objects.filter(
            conversation=conversacion
        ).order_by('created_at')[:50]
        
        context = {
            'persona': persona,
            'conversacion': conversacion,
            'mensajes': mensajes,
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
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error en chatbot_new_conversation: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Error al crear nueva conversación.'
        }, status=500)

