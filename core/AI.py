# core/AI.py
"""
Módulo de análisis de sentimientos usando TensorFlow/Keras.
Procesa comentarios y predice si son positivos o negativos.
"""
import os
import logging
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from django.conf import settings
import json

logger = logging.getLogger(__name__)

# Ruta al directorio del modelo
directorio_modelo = os.path.join(settings.BASE_DIR, 'core', 'AI ZenMindConnect')

# Ruta al archivo del modelo
ruta_modelo_sentimientos = os.path.join(directorio_modelo, 'modelo_sentimientos_tf_despues_de_cargar.h5')

# Ruta al archivo del tokenizador
ruta_tokenizador = os.path.join(directorio_modelo, 'tokenizador.json')

# Variables globales para el modelo y tokenizador (carga lazy)
_modelo_sentimientos = None
_tokenizador = None


def _cargar_modelo():
    """Carga el modelo de TensorFlow de forma lazy."""
    global _modelo_sentimientos
    if _modelo_sentimientos is None:
        try:
            if not os.path.exists(ruta_modelo_sentimientos):
                raise FileNotFoundError(f"Modelo no encontrado en: {ruta_modelo_sentimientos}")
            _modelo_sentimientos = tf.keras.models.load_model(ruta_modelo_sentimientos)
            logger.info("Modelo de sentimientos cargado exitosamente")
        except Exception as e:
            logger.error(f"Error al cargar el modelo: {e}")
            raise
    return _modelo_sentimientos


def _cargar_tokenizador():
    """Carga el tokenizador de forma lazy."""
    global _tokenizador
    if _tokenizador is None:
        try:
            if not os.path.exists(ruta_tokenizador):
                raise FileNotFoundError(f"Tokenizador no encontrado en: {ruta_tokenizador}")
            with open(ruta_tokenizador, 'r', encoding='utf-8') as file:
                tokenizador_config = json.load(file)
                tokenizador_config_str = json.dumps(tokenizador_config)
                _tokenizador = tf.keras.preprocessing.text.tokenizer_from_json(tokenizador_config_str)
            logger.info("Tokenizador cargado exitosamente")
        except Exception as e:
            logger.error(f"Error al cargar el tokenizador: {e}")
            raise
    return _tokenizador


def detectar_palabras_negativas(texto):
    """
    Detecta palabras negativas comunes como sistema de respaldo.
    Retorna True si encuentra palabras negativas.
    """
    texto_lower = texto.lower().strip()
    
    # Lista de palabras y frases negativas comunes en español
    palabras_negativas = [
        'tonto', 'tonta', 'tonte', 'idiota', 'estúpido', 'estúpida', 'estupido', 'estupida',
        'imbécil', 'imbecil', 'imbécil', 'imbeciles', 'imbeciles',
        'malo', 'mala', 'mal', 'horrible', 'terrible', 'pésimo', 'pesimo', 'pésima', 'pesima',
        'odio', 'odiar', 'detesto', 'detestar', 'asco', 'asqueroso', 'asquerosa',
        'basura', 'mierda', 'caca', 'feo', 'fea', 'feísimo', 'feisimo',
        'inútil', 'inutil', 'inútiles', 'inutiles', 'inútil', 'inutil',
        'burro', 'burra', 'ignorante', 'tonto', 'tonta',
        'eres un tonto', 'eres una tonta', 'eres tonto', 'eres tonta',
        'muy mal', 'muy malo', 'muy mala', 'súper mal', 'super mal',
        'no me gusta', 'no me gustó', 'no me gusta', 'no gusta',
        'pésimo', 'pesimo', 'pésima', 'pesima', 'pésimos', 'pesimos',
        'horrible', 'terrible', 'asqueroso', 'asquerosa',
        'basura', 'mierda', 'caca', 'feo', 'fea',
        'inútil', 'inutil', 'burro', 'burra',
        'idiota', 'estúpido', 'estúpida', 'estupido', 'estupida',
        'imbécil', 'imbecil', 'imbécil', 'imbeciles', 'imbeciles',
    ]
    
    # Verificar si alguna palabra negativa está en el texto
    for palabra in palabras_negativas:
        if palabra in texto_lower:
            logger.info(f"Palabra negativa detectada en texto: '{palabra}'")
            return True
    
    return False


def predecir_sentimiento(comentario):
    """
    Predice el sentimiento de un comentario (positivo o negativo).
    Usa el modelo de IA y un sistema de respaldo con palabras clave.
    
    Args:
        comentario: Objeto con atributo 'body' o string con el texto del comentario.
    
    Returns:
        str: 'positivo' o 'negativo'
    
    Raises:
        ValueError: Si el comentario está vacío o es inválido.
        Exception: Si hay un error al procesar el comentario.
    """
    try:
        # Obtener el texto del comentario
        if hasattr(comentario, 'body'):
            texto_comentario = str(comentario.body)
        elif isinstance(comentario, str):
            texto_comentario = comentario
        else:
            texto_comentario = str(comentario)
        
        # Validar que el texto no esté vacío
        if not texto_comentario or not texto_comentario.strip():
            logger.warning("Intento de predecir sentimiento de comentario vacío")
            return "neutro"  # Valor por defecto para comentarios vacíos
        
        # SISTEMA DE RESPALDO: Detectar palabras negativas primero
        if detectar_palabras_negativas(texto_comentario):
            logger.info(f"Comentario detectado como NEGATIVO por palabras clave: '{texto_comentario[:50]}...'")
            return "negativo"
        
        # Cargar modelo y tokenizador
        modelo = _cargar_modelo()
        tokenizador = _cargar_tokenizador()
        
        # Tokenizar el comentario
        comentario_tokenizado = tokenizador.texts_to_sequences([texto_comentario])
        
        if not comentario_tokenizado or not comentario_tokenizado[0]:
            logger.warning(f"No se pudo tokenizar el comentario: '{texto_comentario[:50]}...' - Usando sistema de respaldo")
            # Si no se puede tokenizar, usar el sistema de palabras clave
            if detectar_palabras_negativas(texto_comentario):
                return "negativo"
            return "neutro"
        
        # Obtener la longitud máxima del modelo
        maxlen = modelo.input_shape[1] if len(modelo.input_shape) > 1 else 100
        
        # Padding de la secuencia
        comentario_pad = pad_sequences(comentario_tokenizado, maxlen=maxlen)
        
        # Predecir el sentimiento
        prediccion = modelo.predict(comentario_pad, verbose=0)
        
        # Determinar el sentimiento
        # Si prediccion es un array, tomar el primer valor
        if isinstance(prediccion, (list, tuple)) or hasattr(prediccion, '__len__'):
            valor_prediccion = float(prediccion[0][0] if len(prediccion[0]) > 0 else prediccion[0])
        else:
            valor_prediccion = float(prediccion)
        
        # Usar umbral más bajo para detectar negativos (0.4 en lugar de 0.5)
        sentimiento_predicho = "positivo" if valor_prediccion > 0.4 else "negativo"
        
        logger.info(f"Sentimiento detectado por modelo: {sentimiento_predicho} (confianza: {valor_prediccion:.2f}) para texto: '{texto_comentario[:50]}...'")
        
        # Si el modelo dice positivo pero hay palabras negativas, priorizar las palabras
        if sentimiento_predicho == "positivo" and detectar_palabras_negativas(texto_comentario):
            logger.warning(f"Modelo predijo positivo pero hay palabras negativas. Cambiando a negativo.")
            return "negativo"
        
        return sentimiento_predicho
        
    except Exception as e:
        logger.error(f"Error al predecir sentimiento: {e}", exc_info=True)
        # En caso de error, usar sistema de respaldo
        try:
            if hasattr(comentario, 'body'):
                texto_comentario = str(comentario.body)
            elif isinstance(comentario, str):
                texto_comentario = comentario
            else:
                texto_comentario = str(comentario)
            
            if detectar_palabras_negativas(texto_comentario):
                logger.info("Sistema de respaldo detectó comentario negativo")
                return "negativo"
        except:
            pass
        
        # Retornar un valor por defecto en caso de error
        return "neutro"

