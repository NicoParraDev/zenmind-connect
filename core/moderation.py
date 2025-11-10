"""
Sistema de moderación de contenido para ZenMindConnect.
Previene acoso, bullying, contenido sexual y otros contenidos inapropiados.
"""
import re
import logging
from typing import Tuple, List, Dict
from django.contrib.auth.models import User
from django.db import models
from .models import Post, Comment, Persona

logger = logging.getLogger(__name__)


# ============================================
# LISTAS DE CONTENIDO PROHIBIDO
# ============================================

# Palabras relacionadas con contenido sexual explícito
PALABRAS_SEXUALES = [
    'porn', 'xxx', 'nsfw', 'sexo', 'sexual', 'desnudo', 'desnuda', 'desnudos',
    'nudismo', 'erótico', 'erotica', 'pornografía', 'pornografico',
    'masturb', 'orgasmo', 'penetracion', 'coito', 'genital', 'vagina', 'pene',
    'sexshop', 'sex-shop', 'onlyfans', 'only fans',
    # Contenido sexual implícito (solo frases específicas con contexto sexual)
    'rico tu cuerpo', 'rica tu cuerpo', 'cuerpo rico', 'cuerpo rica'
]

# Palabras relacionadas con acoso y bullying
PALABRAS_ACOSO = [
    'idiota', 'imbécil', 'estúpido', 'estupido', 'tonto', 'tonta', 'retrasado',
    'retrasada', 'loco', 'loca', 'loca de mierda', 'puta', 'puto', 'maricón',
    'maricon', 'marica', 'joto', 'jota', 'culero', 'culera', 'hijo de puta',
    'hija de puta', 'mamón', 'mamona', 'pendejo', 'pendeja', 'cabrón', 'cabrona',
    'mierda', 'carajo', 'chinga', 'chingado', 'joder', 'jodido', 'jodida',
    'muérete', 'muere', 'suicidate', 'suicid', 'matate', 'mata', 'odio',
    'te odio', 'te detesto', 'asqueroso', 'asquerosa', 'feo', 'fea', 'gordo',
    'gorda', 'gordo de mierda', 'gorda de mierda', 'gordo asqueroso',
    'bully', 'bullying', 'acoso', 'acosar', 'hostigar', 'hostigamiento',
    'amenaza', 'amenazar', 'intimidar', 'intimidación', 'humillar', 'humillación',
    # Palabras vulgares adicionales (chilenas y latinoamericanas)
    'xupala', 'xupalo', 'chupala', 'chupalo', 'chupame', 'chupar',
    'verga', 'vergas', 'pito', 'pitos', 'coño', 'coños', 'concha', 'conchas',
    'huevón', 'huevona', 'weon', 'weona', 'wea', 'weas', 'weonaje',
    'huevada', 'huevadas', 'cagada', 'cagadas', 'cagar', 'cagaste',
    'conchetumare', 'conchatumadre', 'ctm', 'ctmre', 'ql', 'qliao', 'qlia',
    'malparido', 'malparida', 'hijueputa', 'hijueputas', 'hdp', 'hijodeputa',
    'carepalo', 'carepaja', 'careverga', 'careculo', 'careculo',
    'mamahuevo', 'mamahuevos', 'mamaguevo', 'mamaguevos',
    'comehuevos', 'comehuevo', 'comegente', 'comegente',
    'huelepedo', 'huelepedos', 'tragaleche', 'tragaleches',
    # Términos adicionales de acoso y groserías
    'gilipollas', 'capullo', 'capulla', 'zoquete', 'zoqueta',
    'tarado', 'tarada', 'mamarracho', 'mamarracha', 'cretino', 'cretina',
    'necio', 'necia', 'conchudo', 'conchuda',
    # Términos discriminatorios y de odio
    'negro de mierda', 'negro asqueroso', 'indio de mierda', 'indio asqueroso',
    'marica', 'maricon', 'joto', 'jota', 'puto', 'puta',
    'gay de mierda', 'lesbiana de mierda', 'trans de mierda',
    # Frases de acoso adicionales
    'vete a la mierda', 'vete al carajo', 'vete al diablo',
    'que te jodan', 'que te chinguen', 'que te den',
    'me cago en', 'me cago en tu', 'me cago en la',
    'me importa un carajo', 'me importa un pito', 'me importa un huevo',
    'me vale madre', 'me vale verga', 'me vale pito'
]

# Palabras relacionadas con violencia
PALABRAS_VIOLENCIA = [
    'matar', 'muerte', 'asesinar', 'asesinato', 'violencia', 'violento',
    'golpear', 'golpe', 'pegar', 'pelea', 'pelear', 'disparar', 'disparo',
    'arma', 'armas', 'cuchillo', 'navaja', 'sangre', 'sangriento', 'tortura',
    'torturar', 'dañar', 'daño', 'herir', 'herida', 'lastimar', 'lastimadura',
    # Términos adicionales de violencia
    'apuñalar', 'apuñalamiento', 'degollar', 'degollamiento',
    'estrangular', 'estrangulación', 'ahogar', 'ahogamiento',
    'quemar', 'quemadura', 'incendiar', 'incendio',
    'violar', 'violación', 'abusar', 'abuso sexual',
    'golpear', 'golpe', 'cachetear', 'cachetada',
    'patada', 'patadas', 'patear', 'pateo',
    'puñetazo', 'puñetazos', 'puñete', 'puñetes'
]

# Palabras relacionadas con drogas ilegales
PALABRAS_DROGAS = [
    'droga', 'drogas', 'marihuana', 'cannabis', 'cocaína', 'cocaina', 'heroína',
    'heroina', 'lsd', 'mdma', 'éxtasis', 'extasis', 'anfetamina', 'crack',
    'metanfetamina', 'fentanilo', 'opio', 'morfina', 'inyectar', 'inyección',
    'fumar', 'fumando', 'drogado', 'drogada', 'colocado', 'colocada', 'high',
    # Términos adicionales de drogas
    'porro', 'porros', 'pito', 'pitillo', 'canuto', 'canutos',
    'coca', 'perico', 'perica', 'pasta base', 'paco',
    'pastilla', 'pastillas', 'trip', 'tripear', 'colocón',
    'drogadicto', 'drogadicta', 'adicto', 'adicta', 'dependiente',
    'inyección', 'inyectarse', 'inyectado', 'inyectada',
    'fumarse', 'fumado', 'fumada', 'fumando'
]

# Palabras relacionadas con contenido no relacionado con bienestar (trolling, spam, etc.)
# NOTA: Los memes, chistes y bromas positivos están permitidos
PALABRAS_MEMES = [
    'troll', 'trolling', 'shitpost', 'shit post', 'bait', 'trolear', 'troleo',
    'spam', 'spamming', 'flood', 'flooding', 'raid', 'raiding'
]

# Frases de acoso y bullying comunes
FRASES_ACOSO = [
    r'te\s+odio',
    r'te\s+detesto',
    r'eres\s+un?\s+(idiota|imbécil|estúpido|tonto|retrasado)',
    r'vete\s+a\s+la\s+mierda',
    r'que\s+te\s+mueras',
    r'ojalá\s+te\s+mueras',
    r'deberías\s+morir',
    r'no\s+deberías\s+existir',
    r'eres\s+inútil',
    r'no\s+sirves\s+para\s+nada',
    r'eres\s+un?\s+fracaso',
    r'mejor\s+suicidate',
    r'deberías\s+suicidarte',
    r'eres\s+un?\s+perdedor',
    r'eres\s+un?\s+basura',
    r'nadie\s+te\s+quiere',
    r'todos\s+te\s+odian',
    r'eres\s+un?\s+desperdicio',
    r'no\s+vales\s+nada',
    r'eres\s+un?\s+asco',
    # Frases adicionales de acoso
    r'vete\s+al\s+carajo',
    r'vete\s+al\s+diablo',
    r'que\s+te\s+jodan',
    r'que\s+te\s+chinguen',
    r'que\s+te\s+den',
    r'me\s+cago\s+en\s+(ti|tu|tu\s+madre|tu\s+familia)',
    r'me\s+importa\s+un\s+(carajo|pito|huevo|verga)',
    r'me\s+vale\s+(madre|verga|pito|huevo)',
    r'chúpame\s+(la|el)',
    r'chúpate\s+(la|el)',
    r'vete\s+a\s+la\s+chingada',
    r'vete\s+a\s+la\s+verga',
    r'que\s+te\s+parta\s+un\s+rayo',
    r'ojalá\s+te\s+parta\s+un\s+rayo',
    r'ojalá\s+te\s+pase\s+algo\s+malo',
    r'deberías\s+desaparecer',
    r'no\s+deberías\s+nacer',
    r'eres\s+un?\s+error',
    r'eres\s+un?\s+desperdicio\s+de\s+oxígeno'
]

# Frases de contenido sexual implícito (solo contextos claramente sexuales)
FRASES_SEXUALES = [
    r'que\s+rico\s+tu\s+cuerpo',
    r'que\s+rica\s+tu\s+cuerpo',
    r'rico\s+tu\s+cuerpo',
    r'rica\s+tu\s+cuerpo',
    r'cuerpo\s+rico',
    r'cuerpo\s+rica',
    r'quiero\s+ver\s+tu\s+cuerpo',
    r'muestrame\s+tu\s+cuerpo',
    r'muéstrame\s+tu\s+cuerpo',
    r'enseñame\s+tu\s+cuerpo',
    r'enséñame\s+tu\s+cuerpo',
    r'quiero\s+tocarte\s+el\s+cuerpo',
    r'quiero\s+tocarte\s+la\s+(pierna|nalga|pecho|pechos)',
    r'te\s+quiero\s+tocar\s+el\s+cuerpo',
    r'te\s+quiero\s+ver\s+desnud',
    r'quiero\s+verte\s+desnud',
    r'desnudate',
    r'desnúdate'
]

# Combinación de todas las palabras prohibidas
TODAS_PALABRAS_PROHIBIDAS = (
    PALABRAS_SEXUALES + 
    PALABRAS_ACOSO + 
    PALABRAS_VIOLENCIA + 
    PALABRAS_DROGAS + 
    PALABRAS_MEMES
)


# ============================================
# FUNCIONES DE MODERACIÓN
# ============================================

def detectar_contenido_inapropiado(texto: str) -> Tuple[bool, List[str], str]:
    """
    Detecta contenido inapropiado en un texto.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        tuple: (es_inapropiado: bool, palabras_encontradas: List[str], categoria: str)
    """
    if not texto:
        return False, [], ""
    
    texto_lower = texto.lower()
    palabras_encontradas = []
    categoria = ""
    
    # Detectar palabras sexuales
    for palabra in PALABRAS_SEXUALES:
        if palabra in texto_lower:
            palabras_encontradas.append(palabra)
            if not categoria:
                categoria = "Contenido sexual explícito"
    
    # Detectar palabras de acoso/bullying
    for palabra in PALABRAS_ACOSO:
        if palabra in texto_lower:
            palabras_encontradas.append(palabra)
            if not categoria:
                categoria = "Acoso o bullying"
    
    # Detectar frases de acoso (usando regex)
    for frase in FRASES_ACOSO:
        if re.search(frase, texto_lower, re.IGNORECASE):
            palabras_encontradas.append(frase)
            if not categoria:
                categoria = "Acoso o bullying"
    
    # Detectar frases sexuales implícitas (usando regex)
    for frase in FRASES_SEXUALES:
        if re.search(frase, texto_lower, re.IGNORECASE):
            palabras_encontradas.append(frase)
            if not categoria:
                categoria = "Contenido sexual explícito"
    
    # Detectar violencia
    if not categoria:
        for palabra in PALABRAS_VIOLENCIA:
            if palabra in texto_lower:
                palabras_encontradas.append(palabra)
                categoria = "Violencia"
                break
    
    # Detectar drogas
    if not categoria:
        for palabra in PALABRAS_DROGAS:
            if palabra in texto_lower:
                palabras_encontradas.append(palabra)
                categoria = "Drogas ilegales"
                break
    
    # Detectar memes
    if not categoria:
        for palabra in PALABRAS_MEMES:
            if palabra in texto_lower:
                palabras_encontradas.append(palabra)
                categoria = "Contenido no relacionado con bienestar"
                break
    
    # Detectar spam de risas excesivas (más de 3 "jaja" consecutivos)
    if not categoria:
        if re.search(r'jajaja{3,}', texto_lower) or texto_lower.count('jaja') > 2:
            palabras_encontradas.append('risas excesivas')
            categoria = "Contenido no relacionado con bienestar"
    
    es_inapropiado = len(palabras_encontradas) > 0
    
    if es_inapropiado:
        logger.warning(
            f"Contenido inapropiado detectado: {categoria}. "
            f"Palabras encontradas: {', '.join(palabras_encontradas[:5])}"
        )
    
    return es_inapropiado, palabras_encontradas, categoria


def validar_post(post: Post) -> Tuple[bool, str]:
    """
    Valida un post completo para contenido inapropiado.
    
    Args:
        post: Instancia de Post
        
    Returns:
        tuple: (es_valido: bool, mensaje_error: str)
    """
    # Combinar todos los campos de texto
    texto_completo = f"{post.title} {post.intro} {post.body}".strip()
    
    es_inapropiado, palabras, categoria = detectar_contenido_inapropiado(texto_completo)
    
    if es_inapropiado:
        mensaje = (
            f"El contenido contiene {categoria.lower()}. "
            f"Por favor, mantén el contenido relacionado con bienestar mental y respeto hacia los demás."
        )
        return False, mensaje
    
    return True, ""


def validar_comentario(comentario: Comment) -> Tuple[bool, str]:
    """
    Valida un comentario para contenido inapropiado.
    
    Args:
        comentario: Instancia de Comment
        
    Returns:
        tuple: (es_valido: bool, mensaje_error: str)
    """
    texto_completo = f"{comentario.name} {comentario.body}".strip()
    
    es_inapropiado, palabras, categoria = detectar_contenido_inapropiado(texto_completo)
    
    if es_inapropiado:
        mensaje = (
            f"El comentario contiene {categoria.lower()}. "
            f"Por favor, mantén un ambiente de respeto y bienestar."
        )
        return False, mensaje
    
    return True, ""


def reportar_contenido(post_id: int = None, comment_id: int = None, 
                       razon: str = "", usuario_reportante: User = None) -> bool:
    """
    Reporta contenido inapropiado.
    
    Args:
        post_id: ID del post a reportar (opcional)
        comment_id: ID del comentario a reportar (opcional)
        razon: Razón del reporte
        usuario_reportante: Usuario que reporta
        
    Returns:
        bool: True si el reporte fue exitoso
    """
    try:
        if post_id:
            post = Post.objects.get(idPost=post_id)
            post.reportado = True
            post.save()
            logger.warning(
                f"Post {post_id} reportado por usuario {usuario_reportante.username if usuario_reportante else 'anónimo'}. "
                f"Razón: {razon}"
            )
            return True
        
        if comment_id:
            comment = Comment.objects.get(id=comment_id)
            comment.reportado = True
            comment.save()
            logger.warning(
                f"Comentario {comment_id} reportado por usuario {usuario_reportante.username if usuario_reportante else 'anónimo'}. "
                f"Razón: {razon}"
            )
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error al reportar contenido: {e}")
        return False


def obtener_posts_reportados() -> List[Post]:
    """Retorna todos los posts reportados que necesitan moderación."""
    return Post.objects.filter(reportado=True, moderado=False).order_by('-date_added')


def moderar_post(post_id: int, aprobar: bool, moderador: User) -> bool:
    """
    Modera un post (aprobar o rechazar).
    
    Args:
        post_id: ID del post
        aprobar: True para aprobar, False para rechazar/eliminar
        moderador: Usuario que modera
        
    Returns:
        bool: True si la moderación fue exitosa
    """
    try:
        post = Post.objects.get(idPost=post_id)
        
        if aprobar:
            post.reportado = False
            post.moderado = True
            post.save()
            logger.info(f"Post {post_id} aprobado por moderador {moderador.username}")
        else:
            # Eliminar el post
            post.delete()
            logger.warning(f"Post {post_id} eliminado por moderador {moderador.username}")
        
        return True
    except Exception as e:
        logger.error(f"Error al moderar post: {e}")
        return False


def obtener_usuarios_problematicos(limite_reportes: int = 3) -> List[Persona]:
    """
    Retorna usuarios que han tenido múltiples posts/comentarios reportados.
    
    Args:
        limite_reportes: Número mínimo de reportes para considerar problemático
        
    Returns:
        List[Persona]: Lista de usuarios problemáticos
    """
    # Contar posts reportados por autor
    posts_reportados = Post.objects.filter(reportado=True).values('author').annotate(
        total_reportes=models.Count('idPost')
    ).filter(total_reportes__gte=limite_reportes)
    
    autores_problematicos = [item['author'] for item in posts_reportados]
    
    return Persona.objects.filter(rut__in=autores_problematicos)


def bloquear_usuario(persona: Persona, razon: str = "") -> bool:
    """
    Bloquea un usuario problemático.
    
    Args:
        persona: Persona a bloquear
        razon: Razón del bloqueo
        
    Returns:
        bool: True si el bloqueo fue exitoso
    """
    try:
        # Desactivar la cuenta de usuario
        if persona.user:
            persona.user.is_active = False
            persona.user.save()
            logger.warning(f"Usuario {persona.rut} bloqueado. Razón: {razon}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error al bloquear usuario: {e}")
        return False

