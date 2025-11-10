"""
Middleware para protección contra bots, scraping y RPA.
Incluye detección de User-Agents sospechosos, rate limiting avanzado,
y verificación de comportamiento humano.
También incluye protección contra ataques de seguridad.
"""
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from core.security import ip_esta_bloqueada, registrar_intento_sospechoso
import logging
import re
import sys

logger = logging.getLogger(__name__)


class AntiBotMiddleware(MiddlewareMixin):
    """
    Middleware para detectar y bloquear bots, scrapers y herramientas RPA.
    """
    
    # User-Agents conocidos de bots y herramientas RPA
    BOT_USER_AGENTS = [
        'bot', 'crawler', 'spider', 'scraper', 'scrape',
        'rocketbot', 'uipath', 'automation', 'selenium',
        'webdriver', 'phantomjs', 'headless', 'puppeteer',
        'playwright', 'scrapy', 'beautifulsoup', 'requests',
        'curl', 'wget', 'python-requests', 'httpclient',
        'apache-httpclient', 'okhttp', 'go-http-client',
        'java/', 'python/', 'node-fetch', 'axios',
        'postman', 'insomnia', 'httpie', 'rest-client',
        'microsoft office', 'libwww-perl', 'lwp-trivial',
        'mechanize', 'urllib', 'httpx', 'aiohttp'
    ]
    
    # Patrones de IPs sospechosas (puedes expandir esto)
    SUSPICIOUS_PATTERNS = [
        r'^0\.0\.0\.',  # IPs inválidas
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Procesa cada request y verifica si es un bot o un ataque.
        """
        # Ignorar en modo test
        from django.conf import settings
        if getattr(settings, 'TESTING', False) or 'test' in sys.argv:
            return None
        
        # Verificar si la IP está bloqueada por intentos de ataque
        if ip_esta_bloqueada(request):
            logger.warning(f"IP bloqueada intentó acceder: {self.get_client_ip(request)}")
            return self._block_request(request, "Tu IP ha sido bloqueada por intentos de ataque.")
        
        # Obtener información del request
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        ip_address = self.get_client_ip(request)
        path = request.path
        
        # Ignorar ciertas rutas (admin, static, etc.)
        if self._should_ignore_path(path):
            return None
        
        # Verificar parámetros GET/POST por patrones sospechosos
        if self._detectar_ataques_en_parametros(request):
            return self._block_request(request, "Parámetros sospechosos detectados")
        
        # Verificar User-Agent
        if self._is_bot_user_agent(user_agent):
            logger.warning(
                f"Bot detectado - IP: {ip_address}, "
                f"User-Agent: {user_agent[:100]}, Path: {path}"
            )
            return self._block_request(request, "User-Agent sospechoso detectado")
        
        # Verificar headers comunes de bots
        if self._has_bot_headers(request):
            logger.warning(
                f"Bot detectado por headers - IP: {ip_address}, Path: {path}"
            )
            return self._block_request(request, "Headers sospechosos detectados")
        
        # Verificar rate limiting avanzado para patrones de scraping
        if self._is_scraping_pattern(request, ip_address):
            logger.warning(
                f"Patrón de scraping detectado - IP: {ip_address}, Path: {path}"
            )
            return self._block_request(request, "Patrón de scraping detectado")
        
        # Verificar si falta JavaScript (muchos bots no ejecutan JS)
        # PERO: Si el usuario está autenticado, no bloquear (es un usuario legítimo)
        # NOTA: request.user puede no existir si AuthenticationMiddleware no se ha ejecutado aún
        # Por eso verificamos con hasattr() antes de acceder
        if self._requires_javascript(request) and not self._has_javascript_token(request):
            # Si el usuario está autenticado, permitir el acceso (es legítimo)
            # Verificar si request.user existe de forma segura
            try:
                if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated'):
                    if request.user.is_authenticated:
                        return None
            except AttributeError:
                # Si request.user no existe aún, continuar con la verificación normal
                pass
            
            # No bloquear inmediatamente, solo marcar como sospechoso
            cache_key = f'suspicious_no_js:{ip_address}'
            suspicious_count = cache.get(cache_key, 0)
            cache.set(cache_key, suspicious_count + 1, 300)  # 5 minutos
            
            if suspicious_count >= 10:
                logger.warning(
                    f"Bloqueado por falta de JavaScript - IP: {ip_address}"
                )
                return self._block_request(request, "JavaScript requerido")
        
        return None
    
    def _should_ignore_path(self, path):
        """Rutas que deben ser ignoradas por el middleware."""
        ignore_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/robots.txt',
            '/sitemap.xml',
        ]
        return any(path.startswith(ignore) for ignore in ignore_paths)
    
    def _is_bot_user_agent(self, user_agent):
        """Verifica si el User-Agent pertenece a un bot conocido."""
        if not user_agent:
            return True  # Sin User-Agent es sospechoso
        
        # Verificar contra lista de bots conocidos
        for bot_pattern in self.BOT_USER_AGENTS:
            if bot_pattern in user_agent:
                return True
        
        # Verificar si es muy corto (bots a veces usan User-Agents cortos)
        if len(user_agent) < 10:
            return True
        
        return False
    
    def _has_bot_headers(self, request):
        """Verifica headers que indican uso de bots."""
        # Bots a menudo no envían ciertos headers
        required_headers = ['HTTP_ACCEPT', 'HTTP_ACCEPT_LANGUAGE']
        
        missing_headers = sum(
            1 for header in required_headers 
            if not request.META.get(header)
        )
        
        # Si faltan más de la mitad de los headers requeridos, es sospechoso
        if missing_headers > len(required_headers) / 2:
            return True
        
        # Verificar headers específicos de bots
        if 'HTTP_X_REQUESTED_WITH' in request.META:
            x_requested_with = request.META.get('HTTP_X_REQUESTED_WITH', '').lower()
            if 'xmlhttprequest' not in x_requested_with and request.method == 'POST':
                # POST sin AJAX puede ser bot
                pass
        
        return False
    
    def _is_scraping_pattern(self, request, ip_address):
        """
        Detecta patrones de scraping basados en frecuencia y rutas.
        """
        # Contar requests por IP en ventana de tiempo
        cache_key = f'scraping_pattern:{ip_address}'
        request_count = cache.get(cache_key, 0)
        
        # Incrementar contador
        cache.set(cache_key, request_count + 1, 60)  # 1 minuto
        
        # Si hay más de 30 requests por minuto, es sospechoso
        if request_count > 30:
            return True
        
        # Verificar si está accediendo a muchas rutas diferentes rápidamente
        paths_key = f'scraping_paths:{ip_address}'
        paths = cache.get(paths_key, set())
        paths.add(request.path)
        cache.set(paths_key, paths, 60)
        
        # Si accede a más de 20 rutas diferentes en 1 minuto, es scraping
        if len(paths) > 20:
            return True
        
        return False
    
    def _requires_javascript(self, request):
        """Determina si la ruta requiere JavaScript."""
        js_required_paths = [
            '/sesion/',
            '/registrar_usuario/',
            '/form_post/',
            '/marcar_consulta/',
        ]
        # Si el usuario está autenticado, no requerir JavaScript para rutas de creación/edición
        # ya que son usuarios legítimos
        # Verificar si request.user existe (puede no existir si AuthenticationMiddleware no se ha ejecutado)
        if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated'):
            try:
                if request.user.is_authenticated:
                    # Excluir rutas de creación/edición de la verificación de JavaScript para usuarios autenticados
                    if '/form_post/' in request.path or '/form_mod_post/' in request.path:
                        return False
            except AttributeError:
                pass
        return any(request.path.startswith(path) for path in js_required_paths)
    
    def _has_javascript_token(self, request):
        """Verifica si el request tiene un token que indica JavaScript activo."""
        # Verificar header HTTP
        js_token_header = request.META.get('HTTP_X_JS_TOKEN')
        if js_token_header == 'active':
            return True
        
        # Verificar cookie
        js_cookie = request.COOKIES.get('js_enabled')
        if js_cookie == '1':
            return True
        
        # Verificar campo en POST (para formularios)
        if request.method == 'POST':
            js_token_post = request.POST.get('js_token')
            if js_token_post == 'active':
                return True
        
        return False
    
    def _block_request(self, request, reason):
        """Bloquea el request y retorna una respuesta apropiada."""
        # Si es AJAX, retornar JSON
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Acceso denegado',
                'message': 'Tu solicitud ha sido bloqueada por medidas de seguridad.'
            }, status=403)
        
        # Si es un navegador normal, retornar HTML
        return HttpResponseForbidden(
            f"""
            <html>
            <head>
                <title>Acceso Denegado</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    h1 {{ color: #d32f2f; }}
                </style>
            </head>
            <body>
                <h1>Acceso Denegado</h1>
                <p>Tu solicitud ha sido bloqueada por medidas de seguridad.</p>
                <p>Si crees que esto es un error, por favor contacta al administrador.</p>
            </body>
            </html>
            """
        )
    
    def _detectar_ataques_en_parametros(self, request):
        """
        Detecta patrones de ataque en parámetros GET y POST.
        
        Returns:
            bool: True si detecta un ataque
        """
        from core.security import detectar_sql_injection, detectar_command_injection
        
        # Campos que pueden contener contenido legítimo que podría parecer sospechoso
        # pero que son seguros porque se validan en el formulario
        campos_excluidos = [
            'body',  # Contenido HTML del editor (se sanitiza con bleach)
            'video_url',  # URLs de YouTube/Vimeo (se validan en el formulario)
            'imagen',  # Archivos de imagen (se validan en el formulario)
            'csrfmiddlewaretoken',  # Token CSRF
            'js_token',  # Token de JavaScript
        ]
        
        # Verificar parámetros GET
        for key, value in request.GET.items():
            if key in campos_excluidos:
                continue
            if isinstance(value, str):
                if detectar_sql_injection(value):
                    registrar_intento_sospechoso(
                        request,
                        "SQL_INJECTION",
                        f"Parámetro GET '{key}': {value[:100]}"
                    )
                    return True
                
                if detectar_command_injection(value):
                    registrar_intento_sospechoso(
                        request,
                        "COMMAND_INJECTION",
                        f"Parámetro GET '{key}': {value[:100]}"
                    )
                    return True
        
        # Verificar parámetros POST
        if request.method == 'POST':
            for key, value in request.POST.items():
                # Excluir campos que sabemos que son legítimos
                if key in campos_excluidos:
                    continue
                if isinstance(value, str):
                    if detectar_sql_injection(value):
                        registrar_intento_sospechoso(
                            request,
                            "SQL_INJECTION",
                            f"Parámetro POST '{key}': {value[:100]}"
                        )
                        return True
                    
                    if detectar_command_injection(value):
                        registrar_intento_sospechoso(
                            request,
                            "COMMAND_INJECTION",
                            f"Parámetro POST '{key}': {value[:100]}"
                        )
                        return True
        
        return False
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

