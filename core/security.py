"""
Módulo de seguridad para ZenMindConnect.
Incluye funciones para sanitización, validación y protección contra ataques.
"""
import re
import logging
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.db import connection

logger = logging.getLogger(__name__)


# ============================================
# PROTECCIÓN CONTRA SQL INJECTION
# ============================================

def detectar_sql_injection(texto):
    """
    Detecta patrones sospechosos de SQL injection en un texto.
    
    Args:
        texto: String a analizar
    
    Returns:
        bool: True si detecta patrones sospechosos
    """
    if not texto:
        return False
    
    texto_lower = texto.lower()
    
    # Patrones comunes de SQL injection
    patrones_peligrosos = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(\balter\b.*\btable\b)",
        r"(\bexec\b|\bexecute\b)",
        r"(\bscript\b.*\b>.*<)",
        r"(--|\#|\/\*|\*\/)",  # Comentarios SQL
        r"(\bor\b.*=.*\bor\b)",
        r"(\band\b.*=.*\band\b)",
        r"('.*'.*or.*'.*')",
        r"(\bor\b.*1.*=.*1)",
        r"(\band\b.*1.*=.*1)",
        r"(;.*--|;.*\#|;.*\/\*)",
        r"(\bwaitfor\b.*delay\b)",
        r"(\bxp_cmdshell\b)",
        r"(\bchar\b.*\(.*\))",
        r"(\bcast\b|\bconvert\b)",
    ]
    
    for patron in patrones_peligrosos:
        if re.search(patron, texto_lower, re.IGNORECASE):
            logger.warning(f"Posible SQL injection detectado: {texto[:100]}")
            return True
    
    return False


def validar_sin_sql_injection(texto, campo_nombre="campo"):
    """
    Valida que un texto no contenga patrones de SQL injection.
    
    Args:
        texto: String a validar
        campo_nombre: Nombre del campo para mensajes de error
    
    Returns:
        str: Texto validado
    
    Raises:
        ValidationError: Si se detecta SQL injection
    """
    if not texto:
        return texto
    
    if detectar_sql_injection(str(texto)):
        logger.error(f"Intento de SQL injection bloqueado en campo '{campo_nombre}': {texto[:100]}")
        raise ValidationError(
            f"El campo '{campo_nombre}' contiene caracteres o patrones no permitidos por seguridad."
        )
    
    return texto


# ============================================
# PROTECCIÓN CONTRA XSS (Cross-Site Scripting)
# ============================================

def sanitizar_html(texto, permitir_html_basico=False):
    """
    Sanitiza HTML para prevenir XSS attacks.
    
    Args:
        texto: String a sanitizar
        permitir_html_basico: Si True, permite tags HTML básicos seguros
    
    Returns:
        str: Texto sanitizado
    """
    if not texto:
        return ""
    
    texto_str = str(texto)
    
    # Si no se permite HTML, escapar todo
    if not permitir_html_basico:
        return escape(texto_str)
    
    # Tags HTML permitidos (muy restrictivo)
    tags_permitidos = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    
    # Remover todos los tags excepto los permitidos
    patron = r'<(?!\/?(?:' + '|'.join(tags_permitidos) + r')\b)[^>]*>'
    texto_sanitizado = re.sub(patron, '', texto_str)
    
    # Escapar atributos peligrosos
    texto_sanitizado = re.sub(
        r'on\w+\s*=\s*["\'][^"\']*["\']',
        '',
        texto_sanitizado,
        flags=re.IGNORECASE
    )
    
    # Remover javascript: y data: URLs
    texto_sanitizado = re.sub(
        r'(javascript|data|vbscript):',
        '',
        texto_sanitizado,
        flags=re.IGNORECASE
    )
    
    return texto_sanitizado


def validar_sin_xss(texto, campo_nombre="campo"):
    """
    Valida que un texto no contenga código XSS.
    
    Args:
        texto: String a validar
        campo_nombre: Nombre del campo para mensajes de error
    
    Returns:
        str: Texto validado y sanitizado
    
    Raises:
        ValidationError: Si se detecta XSS
    """
    if not texto:
        return texto
    
    texto_str = str(texto)
    
    # Patrones XSS comunes
    patrones_xss = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<link[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'expression\s*\(',
        r'vbscript:',
        r'data:text/html',
    ]
    
    for patron in patrones_xss:
        if re.search(patron, texto_str, re.IGNORECASE | re.DOTALL):
            logger.warning(f"Posible XSS detectado en campo '{campo_nombre}': {texto[:100]}")
            raise ValidationError(
                f"El campo '{campo_nombre}' contiene código no permitido por seguridad."
            )
    
    # Sanitizar el texto
    return sanitizar_html(texto_str, permitir_html_basico=False)


# ============================================
# PROTECCIÓN CONTRA PATH TRAVERSAL
# ============================================

def validar_path_seguro(path):
    """
    Valida que un path no contenga caracteres peligrosos para path traversal.
    
    Args:
        path: String con el path a validar
    
    Returns:
        str: Path validado
    
    Raises:
        ValidationError: Si el path es peligroso
    """
    if not path:
        return path
    
    path_str = str(path)
    
    # Caracteres peligrosos
    caracteres_peligrosos = ['..', '/', '\\', '\x00']
    
    for char in caracteres_peligrosos:
        if char in path_str:
            logger.warning(f"Path traversal detectado: {path_str}")
            raise ValidationError("El path contiene caracteres no permitidos por seguridad.")
    
    return path_str


# ============================================
# PROTECCIÓN CONTRA COMMAND INJECTION
# ============================================

def detectar_command_injection(texto):
    """
    Detecta patrones de command injection.
    
    Args:
        texto: String a analizar
    
    Returns:
        bool: True si detecta patrones sospechosos
    """
    if not texto:
        return False
    
    texto_str = str(texto)
    
    # Patrones de command injection
    patrones_peligrosos = [
        r'[;&|`$]',  # Separadores de comandos
        r'\$\(',  # Command substitution
        r'`.*`',  # Backticks
        r'\|\s*\w+',  # Pipes
        r'&&\s*\w+',  # AND operators
        r'\|\|\s*\w+',  # OR operators
        r';\s*\w+',  # Semicolon
        r'<\(',  # Process substitution
        r'>\(',  # Process substitution
    ]
    
    for patron in patrones_peligrosos:
        if re.search(patron, texto_str):
            logger.warning(f"Posible command injection detectado: {texto_str[:100]}")
            return True
    
    return False


def validar_sin_command_injection(texto, campo_nombre="campo"):
    """
    Valida que un texto no contenga patrones de command injection.
    
    Args:
        texto: String a validar
        campo_nombre: Nombre del campo para mensajes de error
    
    Returns:
        str: Texto validado
    
    Raises:
        ValidationError: Si se detecta command injection
    """
    if not texto:
        return texto
    
    if detectar_command_injection(str(texto)):
        logger.error(f"Intento de command injection bloqueado en campo '{campo_nombre}'")
        raise ValidationError(
            f"El campo '{campo_nombre}' contiene caracteres no permitidos por seguridad."
        )
    
    return texto


# ============================================
# VALIDACIÓN DE ARCHIVOS
# ============================================

def validar_tipo_archivo(archivo, tipos_permitidos=None, max_tamaño_mb=10):
    """
    Valida el tipo y tamaño de un archivo subido.
    
    Args:
        archivo: Objeto de archivo de Django (puede ser UploadedFile o ImageFieldFile)
        tipos_permitidos: Lista de tipos MIME permitidos (None = solo imágenes)
        max_tamaño_mb: Tamaño máximo en MB
    
    Returns:
        tuple: (es_valido: bool, mensaje_error: str)
    """
    if not archivo:
        return True, ""
    
    # Si es un ImageFieldFile (archivo existente del modelo), no necesita validación
    # Solo validar archivos nuevos que tienen content_type
    if not hasattr(archivo, 'content_type'):
        # Es un ImageFieldFile existente, no necesita validación
        return True, ""
    
    # Tipos permitidos por defecto (solo imágenes)
    if tipos_permitidos is None:
        tipos_permitidos = [
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/gif',
            'image/webp'
        ]
    
    # Validar tipo MIME
    tipo_mime = archivo.content_type
    if tipo_mime not in tipos_permitidos:
        logger.warning(f"Tipo de archivo no permitido: {tipo_mime}")
        return False, f"Tipo de archivo no permitido. Solo se permiten: {', '.join(tipos_permitidos)}"
    
    # Validar tamaño
    tamaño_mb = archivo.size / (1024 * 1024)
    if tamaño_mb > max_tamaño_mb:
        logger.warning(f"Archivo demasiado grande: {tamaño_mb:.2f}MB")
        return False, f"El archivo es demasiado grande. Tamaño máximo: {max_tamaño_mb}MB"
    
    # Validar extensión del nombre de archivo
    nombre_archivo = archivo.name.lower()
    extensiones_permitidas = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if not any(nombre_archivo.endswith(ext) for ext in extensiones_permitidas):
        return False, "Extensión de archivo no permitida."
    
    return True, ""


# ============================================
# VALIDACIÓN DE ENTRADAS GENERALES
# ============================================

def validar_entrada_segura(texto, campo_nombre="campo", max_longitud=1000):
    """
    Valida una entrada de forma segura contra múltiples ataques.
    
    Args:
        texto: String a validar
        campo_nombre: Nombre del campo
        max_longitud: Longitud máxima permitida
    
    Returns:
        str: Texto validado y sanitizado
    
    Raises:
        ValidationError: Si la entrada es peligrosa
    """
    if not texto:
        return texto
    
    texto_str = str(texto)
    
    # Validar longitud
    if len(texto_str) > max_longitud:
        raise ValidationError(
            f"El campo '{campo_nombre}' excede la longitud máxima de {max_longitud} caracteres."
        )
    
    # Validar contra SQL injection
    validar_sin_sql_injection(texto_str, campo_nombre)
    
    # Validar contra XSS
    texto_str = validar_sin_xss(texto_str, campo_nombre)
    
    # Validar contra command injection
    validar_sin_command_injection(texto_str, campo_nombre)
    
    return texto_str


# ============================================
# LOGGING DE INTENTOS SOSPECHOSOS
# ============================================

def registrar_intento_sospechoso(request, tipo_ataque, detalles=""):
    """
    Registra un intento de ataque sospechoso en los logs.
    
    Args:
        request: HttpRequest object
        tipo_ataque: Tipo de ataque detectado (SQL_INJECTION, XSS, etc.)
        detalles: Detalles adicionales del intento
    """
    ip_address = request.META.get('REMOTE_ADDR', 'Desconocida')
    user_agent = request.META.get('HTTP_USER_AGENT', 'Desconocido')
    path = request.path
    metodo = request.method
    
    logger.critical(
        f"⚠️ INTENTO DE ATAQUE DETECTADO ⚠️\n"
        f"Tipo: {tipo_ataque}\n"
        f"IP: {ip_address}\n"
        f"User-Agent: {user_agent}\n"
        f"Path: {path}\n"
        f"Método: {metodo}\n"
        f"Detalles: {detalles}\n"
        f"Usuario: {request.user.username if request.user.is_authenticated else 'Anónimo'}"
    )
    
    # También guardar en cache para rate limiting adicional
    from django.core.cache import cache
    cache_key = f'attack_attempt:{ip_address}:{tipo_ataque}'
    intentos = cache.get(cache_key, 0)
    cache.set(cache_key, intentos + 1, 3600)  # 1 hora
    
    # Si hay más de 5 intentos, bloquear IP
    if intentos >= 5:
        logger.critical(f"🚨 IP BLOQUEADA POR MÚLTIPLES INTENTOS DE ATAQUE: {ip_address}")
        cache.set(f'ip_blocked:{ip_address}', True, 86400)  # Bloquear por 24 horas


# ============================================
# VERIFICACIÓN DE IP BLOQUEADA
# ============================================

def ip_esta_bloqueada(request):
    """
    Verifica si la IP está bloqueada por intentos de ataque.
    
    Args:
        request: HttpRequest object
    
    Returns:
        bool: True si la IP está bloqueada
    """
    from django.core.cache import cache
    ip_address = request.META.get('REMOTE_ADDR', '')
    return cache.get(f'ip_blocked:{ip_address}', False)

