"""
Sistema de Chatbot con OpenAI API para ZenMindConnect.
Proporciona soporte inicial y recomendaciones de psicólogos.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from decouple import config
from .models import Persona, Psicologo, Especialidad, ChatConversation, ChatMessageBot
from django.utils import timezone

logger = logging.getLogger(__name__)

# Configuración de OpenAI
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
OPENAI_MODEL = config('OPENAI_MODEL', default='gpt-3.5-turbo')

# Palabras clave de crisis (requieren derivación inmediata a profesional)
PALABRAS_CRISIS = [
    'suicidio', 'suicidar', 'matarme', 'morirme', 'acabar con todo',
    'no quiero vivir', 'quiero morir', 'mejor muerto', 'sin sentido',
    'autolesión', 'cortarme', 'herirme', 'lastimarme',
    'crisis', 'emergencia', 'ayuda urgente', 'necesito ayuda ya',
    'no puedo más', 'no aguanto', 'no soporto', 'estoy desesperado',
    'pensamientos de muerte', 'planes de suicidio'
]


def detectar_crisis(texto: str) -> bool:
    """
    Detecta si el mensaje contiene indicadores de crisis.
    
    Args:
        texto: Texto del mensaje del usuario
        
    Returns:
        bool: True si se detecta crisis
    """
    if not texto:
        return False
    
    texto_lower = texto.lower()
    
    for palabra in PALABRAS_CRISIS:
        if palabra in texto_lower:
            logger.warning(f"Crisis detectada en mensaje: {palabra}")
            return True
    
    return False


def obtener_psicologo_recomendado(texto: str, persona: Persona) -> Optional[Psicologo]:
    """
    Recomienda un psicólogo basado en el contenido del mensaje.
    
    Args:
        texto: Mensaje del usuario
        persona: Usuario que necesita recomendación
        
    Returns:
        Psicologo o None
    """
    try:
        texto_lower = texto.lower()
        
        # Mapeo de palabras clave a especialidades
        especialidades_keywords = {
            'ansiedad': ['ansiedad', 'ansioso', 'nervioso', 'preocupado', 'pánico'],
            'depresion': ['depresión', 'deprimido', 'triste', 'desanimado', 'sin energía'],
            'estres': ['estrés', 'estresado', 'presión', 'agobiado'],
            'relaciones': ['relación', 'pareja', 'familia', 'conflicto', 'comunicación'],
            'trauma': ['trauma', 'abuso', 'violencia', 'acoso', 'bullying'],
            'adicciones': ['adicción', 'drogas', 'alcohol', 'dependencia'],
            'duelo': ['duelo', 'pérdida', 'muerte', 'fallecimiento', 'luto'],
        }
        
        # Buscar especialidad más relevante
        especialidad_encontrada = None
        max_coincidencias = 0
        
        for especialidad_nombre, keywords in especialidades_keywords.items():
            coincidencias = sum(1 for keyword in keywords if keyword in texto_lower)
            if coincidencias > max_coincidencias:
                max_coincidencias = coincidencias
                try:
                    especialidad_encontrada = Especialidad.objects.get(nombre__icontains=especialidad_nombre)
                except Especialidad.DoesNotExist:
                    continue
        
        # Si encontramos especialidad, buscar psicólogo
        if especialidad_encontrada:
            psicologos = Psicologo.objects.filter(especialidad=especialidad_encontrada, psicologo__isnull=False)
            if psicologos.exists():
                return psicologos.first()
        
        # Si no hay coincidencia específica, retornar cualquier psicólogo disponible
        psicologos = Psicologo.objects.all()
        if psicologos.exists():
            return psicologos.first()
        
        return None
        
    except Exception as e:
        logger.error(f"Error al obtener psicólogo recomendado: {e}")
        return None


def obtener_conversacion_activa(persona: Persona) -> ChatConversation:
    """
    Obtiene o crea una conversación activa para el usuario.
    
    Args:
        persona: Usuario
        
    Returns:
        ChatConversation
    """
    conversacion = ChatConversation.objects.filter(
        persona=persona,
        is_active=True
    ).order_by('-updated_at').first()
    
    if not conversacion:
        conversacion = ChatConversation.objects.create(
            persona=persona,
            is_active=True
        )
        logger.info(f"Nueva conversación creada para {persona}")
    
    return conversacion


def obtener_historial_mensajes(conversacion: ChatConversation, limite: int = 20) -> List[Dict]:
    """
    Obtiene el historial de mensajes de la conversación en formato para OpenAI.
    
    Args:
        conversacion: Conversación
        limite: Número máximo de mensajes a retornar
        
    Returns:
        Lista de mensajes en formato OpenAI
    """
    mensajes = ChatMessageBot.objects.filter(
        conversation=conversacion
    ).order_by('created_at')[:limite]
    
    historial = []
    for msg in mensajes:
        historial.append({
            'role': msg.role,
            'content': msg.message
        })
    
    return historial


def crear_mensaje_sistema() -> Dict:
    """
    Crea el mensaje del sistema para el chatbot.
    
    Returns:
        Dict con el mensaje del sistema
    """
    return {
        'role': 'system',
        'content': """Eres un asistente virtual de bienestar mental para ZenMindConnect, una plataforma que conecta personas con psicólogos profesionales.

Tu rol es:
1. Escuchar y empatizar con los usuarios
2. Proporcionar información general sobre bienestar mental
3. Recomendar cuando es apropiado consultar con un profesional
4. Detectar situaciones de crisis y derivar inmediatamente a ayuda profesional
5. Responder preguntas sobre la plataforma y sus servicios

IMPORTANTE:
- Si detectas indicadores de crisis (suicidio, autolesión, emergencia), debes recomendar inmediatamente contactar a un profesional o línea de crisis
- No debes diagnosticar ni dar consejos médicos específicos
- Siempre enfatiza la importancia de consultar con profesionales para problemas serios
- Sé empático, comprensivo y profesional
- Responde en español
- Mantén las respuestas concisas pero útiles"""
    }


def enviar_mensaje_openai(mensaje_usuario: str, historial: List[Dict]) -> Tuple[str, bool]:
    """
    Envía un mensaje a OpenAI y obtiene la respuesta.
    
    Args:
        mensaje_usuario: Mensaje del usuario
        historial: Historial de mensajes anteriores
        
    Returns:
        Tuple: (respuesta, es_crisis)
    """
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY no configurada")
        return "Lo siento, el servicio de chatbot no está disponible en este momento. Por favor, contacta directamente con un psicólogo.", False
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Construir mensajes para OpenAI
        mensajes = [crear_mensaje_sistema()]
        mensajes.extend(historial)
        mensajes.append({
            'role': 'user',
            'content': mensaje_usuario
        })
        
        # Llamar a OpenAI
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=mensajes,
            max_tokens=500,
            temperature=0.7,
        )
        
        respuesta = response.choices[0].message.content.strip()
        
        # Detectar si la respuesta sugiere crisis
        es_crisis = detectar_crisis(mensaje_usuario) or detectar_crisis(respuesta)
        
        return respuesta, es_crisis
        
    except ImportError:
        logger.error("OpenAI library no instalada. Ejecuta: pip install openai")
        return "Lo siento, el servicio de chatbot no está disponible. Por favor, contacta directamente con un psicólogo.", False
    except Exception as e:
        logger.error(f"Error al llamar a OpenAI: {e}")
        return "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta nuevamente o contacta directamente con un psicólogo.", False


def procesar_mensaje_chatbot(persona: Persona, mensaje: str) -> Dict:
    """
    Procesa un mensaje del usuario y retorna la respuesta del chatbot.
    
    Args:
        persona: Usuario que envía el mensaje
        mensaje: Mensaje del usuario
        
    Returns:
        Dict con respuesta, crisis detectada, y psicólogo recomendado
    """
    try:
        # Obtener o crear conversación activa
        conversacion = obtener_conversacion_activa(persona)
        
        # Guardar mensaje del usuario
        mensaje_usuario = ChatMessageBot.objects.create(
            conversation=conversacion,
            role='user',
            message=mensaje
        )
        
        # Detectar crisis
        es_crisis = detectar_crisis(mensaje)
        
        # Obtener historial
        historial = obtener_historial_mensajes(conversacion)
        
        # Obtener respuesta de OpenAI
        respuesta, crisis_en_respuesta = enviar_mensaje_openai(mensaje, historial)
        
        es_crisis = es_crisis or crisis_en_respuesta
        
        # Obtener psicólogo recomendado si es necesario
        psicologo_recomendado = None
        if es_crisis or 'psicólogo' in mensaje.lower() or 'terapia' in mensaje.lower():
            psicologo_recomendado = obtener_psicologo_recomendado(mensaje, persona)
        
        # Guardar respuesta del asistente
        mensaje_asistente = ChatMessageBot.objects.create(
            conversation=conversacion,
            role='assistant',
            message=respuesta,
            is_crisis_detected=es_crisis,
            psicologo_recomendado=psicologo_recomendado
        )
        
        # Actualizar timestamp de conversación
        conversacion.updated_at = timezone.now()
        conversacion.save()
        
        return {
            'respuesta': respuesta,
            'es_crisis': es_crisis,
            'psicologo_recomendado': psicologo_recomendado,
            'conversacion_id': conversacion.id
        }
        
    except Exception as e:
        logger.error(f"Error al procesar mensaje del chatbot: {e}", exc_info=True)
        return {
            'respuesta': 'Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta nuevamente.',
            'es_crisis': False,
            'psicologo_recomendado': None,
            'conversacion_id': None
        }

