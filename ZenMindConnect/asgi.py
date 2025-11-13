"""
ASGI config for ZenMindConnect project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

# IMPORTANTE: Configurar Django ANTES de importar cualquier cosa que use Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ZenMindConnect.settings')

# Inicializar Django ASGI application PRIMERO
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

# Ahora podemos importar cosas que dependen de Django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import core.routing

# Configurar routing para WebSockets
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            core.routing.websocket_urlpatterns
        )
    ),
})
