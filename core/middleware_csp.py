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
            
            # Construir CSP header
            if hasattr(settings, 'CSP_DEFAULT_SRC'):
                csp_parts.append(f"default-src {settings.CSP_DEFAULT_SRC}")
            if hasattr(settings, 'CSP_SCRIPT_SRC'):
                csp_parts.append(f"script-src {settings.CSP_SCRIPT_SRC}")
            if hasattr(settings, 'CSP_STYLE_SRC'):
                csp_parts.append(f"style-src {settings.CSP_STYLE_SRC}")
            if hasattr(settings, 'CSP_FONT_SRC'):
                csp_parts.append(f"font-src {settings.CSP_FONT_SRC}")
            if hasattr(settings, 'CSP_IMG_SRC'):
                csp_parts.append(f"img-src {settings.CSP_IMG_SRC}")
            if hasattr(settings, 'CSP_CONNECT_SRC'):
                csp_parts.append(f"connect-src {settings.CSP_CONNECT_SRC}")
            if hasattr(settings, 'CSP_FRAME_SRC'):
                csp_parts.append(f"frame-src {settings.CSP_FRAME_SRC}")
            if hasattr(settings, 'CSP_FRAME_ANCESTORS'):
                csp_parts.append(f"frame-ancestors {settings.CSP_FRAME_ANCESTORS}")
            
            if csp_parts:
                response['Content-Security-Policy'] = '; '.join(csp_parts)
        
        return response

