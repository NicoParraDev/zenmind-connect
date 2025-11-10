"""
Decoradores personalizados para ZenMindConnect.
Incluye rate limiting y otras utilidades de seguridad.
"""
from functools import wraps
from django.core.cache import cache
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)


def rate_limit(max_attempts=5, window=300, key_prefix='rate_limit'):
    """
    Decorador para limitar el número de intentos por IP o usuario.
    
    Args:
        max_attempts: Número máximo de intentos permitidos (default: 5)
        window: Ventana de tiempo en segundos (default: 300 = 5 minutos)
        key_prefix: Prefijo para la clave de cache
    
    Returns:
        Decorador que aplica rate limiting
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Obtener la IP del cliente
            ip_address = get_client_ip(request)
            
            # Crear clave única para esta IP
            cache_key = f'{key_prefix}:{ip_address}'
            
            # Obtener el número de intentos actuales
            attempts = cache.get(cache_key, 0)
            
            # Si se excedió el límite, bloquear el acceso
            if attempts >= max_attempts:
                logger.warning(
                    f"Rate limit excedido para IP {ip_address}. "
                    f"Intentos: {attempts}/{max_attempts} en {window}s"
                )
                messages.error(
                    request,
                    f'Demasiados intentos fallidos. Por favor, espera {window // 60} minutos antes de intentar nuevamente.'
                )
                return redirect('log')
            
            # Ejecutar la vista
            response = view_func(request, *args, **kwargs)
            
            # Si la autenticación falló, incrementar el contador
            if hasattr(request, 'login_failed') and request.login_failed:
                attempts = cache.get(cache_key, 0)
                cache.set(cache_key, attempts + 1, window)
                logger.info(
                    f"Intento de login fallido para IP {ip_address}. "
                    f"Intentos: {attempts + 1}/{max_attempts}"
                )
            else:
                # Si el login fue exitoso, limpiar el contador
                cache.delete(cache_key)
            
            return response
        
        return wrapper
    return decorator


def get_client_ip(request):
    """
    Obtiene la dirección IP real del cliente.
    Considera proxies y headers HTTP.
    
    Args:
        request: Objeto HttpRequest de Django
    
    Returns:
        str: Dirección IP del cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def rate_limit_by_username(max_attempts=5, window=300, key_prefix='rate_limit_user'):
    """
    Decorador para limitar intentos por nombre de usuario.
    Útil para proteger contra ataques dirigidos a usuarios específicos.
    
    Args:
        max_attempts: Número máximo de intentos permitidos (default: 5)
        window: Ventana de tiempo en segundos (default: 300 = 5 minutos)
        key_prefix: Prefijo para la clave de cache
    
    Returns:
        Decorador que aplica rate limiting por usuario
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Solo aplicar si es POST (intento de login)
            if request.method == 'POST':
                username = request.POST.get('username', '').strip()
                
                if username:
                    # Crear clave única para este usuario
                    cache_key = f'{key_prefix}:{username}'
                    
                    # Obtener el número de intentos actuales
                    attempts = cache.get(cache_key, 0)
                    
                    # Si se excedió el límite, bloquear el acceso
                    if attempts >= max_attempts:
                        logger.warning(
                            f"Rate limit excedido para usuario '{username}'. "
                            f"Intentos: {attempts}/{max_attempts} en {window}s"
                        )
                        messages.error(
                            request,
                            f'Demasiados intentos fallidos para este usuario. '
                            f'Por favor, espera {window // 60} minutos antes de intentar nuevamente.'
                        )
                        return redirect('log')
            
            # Ejecutar la vista
            response = view_func(request, *args, **kwargs)
            
            # Si la autenticación falló, incrementar el contador
            if request.method == 'POST' and hasattr(request, 'login_failed') and request.login_failed:
                username = request.POST.get('username', '').strip()
                if username:
                    cache_key = f'{key_prefix}:{username}'
                    attempts = cache.get(cache_key, 0)
                    cache.set(cache_key, attempts + 1, window)
                    logger.info(
                        f"Intento de login fallido para usuario '{username}'. "
                        f"Intentos: {attempts + 1}/{max_attempts}"
                    )
            else:
                # Si el login fue exitoso, limpiar el contador
                if request.method == 'POST':
                    username = request.POST.get('username', '').strip()
                    if username:
                        cache_key = f'{key_prefix}:{username}'
                        cache.delete(cache_key)
            
            return response
        
        return wrapper
    return decorator

