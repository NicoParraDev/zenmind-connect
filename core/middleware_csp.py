"""
Middleware para Content Security Policy (CSP)
Protección avanzada contra XSS
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CSPMiddleware(MiddlewareMixin):
    """
    Middleware para agregar headers de Content Security Policy.
    """
    
    def process_response(self, request, response):
        """Agrega headers CSP a la respuesta."""
        # Solo agregar CSP si está configurado
        if hasattr(settings, 'CSP_DEFAULT_SRC'):
            csp_parts = []
            
            # Para páginas de videollamada, usar CSP más permisivo para Agora
            is_videocall_page = '/videocall/' in request.path
            
            # Construir CSP header
            if hasattr(settings, 'CSP_DEFAULT_SRC'):
                csp_parts.append(f"default-src {settings.CSP_DEFAULT_SRC}")
            if hasattr(settings, 'CSP_SCRIPT_SRC'):
                # Para videollamadas, agregar 'unsafe-eval' para WebAssembly
                script_src = settings.CSP_SCRIPT_SRC
                if is_videocall_page and 'unsafe-eval' not in script_src:
                    script_src = f"{script_src} 'unsafe-eval'"
                csp_parts.append(f"script-src {script_src}")
            if hasattr(settings, 'CSP_STYLE_SRC'):
                csp_parts.append(f"style-src {settings.CSP_STYLE_SRC}")
            if hasattr(settings, 'CSP_FONT_SRC'):
                csp_parts.append(f"font-src {settings.CSP_FONT_SRC}")
            if hasattr(settings, 'CSP_IMG_SRC'):
                csp_parts.append(f"img-src {settings.CSP_IMG_SRC}")
            
            # CSP_CONNECT_SRC - más permisivo para videollamadas
            if hasattr(settings, 'CSP_CONNECT_SRC'):
                if is_videocall_page:
                    # Para videollamadas, permitir conexiones HTTPS/WSS (necesario para Agora)
                    # Agora usa múltiples subdominios dinámicos que no podemos listar todos
                    connect_src = f"{settings.CSP_CONNECT_SRC} https: wss:"
                    csp_parts.append(f"connect-src {connect_src}")
                else:
                    csp_parts.append(f"connect-src {settings.CSP_CONNECT_SRC}")
            
            if hasattr(settings, 'CSP_FRAME_SRC'):
                csp_parts.append(f"frame-src {settings.CSP_FRAME_SRC}")
            if hasattr(settings, 'CSP_FRAME_ANCESTORS'):
                csp_parts.append(f"frame-ancestors {settings.CSP_FRAME_ANCESTORS}")
            
            if csp_parts:
                response['Content-Security-Policy'] = '; '.join(csp_parts)
        
        return response

