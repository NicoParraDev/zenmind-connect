# core/comment_processing.py
"""
Módulo para procesar comentarios y detectar sentimientos.
"""
import logging
from .AI import predecir_sentimiento
from .models import Notificacion

logger = logging.getLogger(__name__)


def procesar_comentario(comentario):
    """
    Procesa un comentario y predice su sentimiento.
    
    Args:
        comentario: Instancia del modelo Comment con atributo 'body'.
    
    Returns:
        str: Sentimiento predicho ('positivo', 'negativo', o 'neutro').
    """
    try:
        texto_comentario = str(comentario.body) if hasattr(comentario, 'body') else str(comentario)
        logger.info(f"Procesando comentario ID: {comentario.id}")
        logger.info(f"Contenido completo del comentario: '{texto_comentario}'")
        
        # Utiliza la función predefinida para predecir el sentimiento
        sentimiento_predicho = predecir_sentimiento(comentario)
        
        logger.info(f"RESULTADO FINAL - Sentimiento detectado: {sentimiento_predicho} para comentario: '{texto_comentario[:100]}...'")
        return sentimiento_predicho
        
    except Exception as e:
        logger.error(f"Error al procesar comentario: {e}", exc_info=True)
        # Intentar detectar palabras negativas como último recurso
        try:
            texto_comentario = str(comentario.body) if hasattr(comentario, 'body') else str(comentario)
            from .AI import detectar_palabras_negativas
            if detectar_palabras_negativas(texto_comentario):
                logger.warning("Sistema de respaldo detectó comentario negativo después de error")
                return "negativo"
        except:
            pass
        return "neutro"  # Valor por defecto en caso de error