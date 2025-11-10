"""
Context processors para agregar variables globales a todos los templates.
"""
from .models import Notificacion, NotificacionSuperusuario


def notificaciones(request):
    """
    Agrega las notificaciones del usuario y del superusuario al contexto global.
    """
    context = {
        'notificaciones_no_leidas': [],
        'notificaciones_superusuario_no_leidas': [],
    }
    
    if request.user.is_authenticated:
        # Notificaciones del usuario normal
        if hasattr(request.user, 'persona'):
            try:
                persona = request.user.persona
                context['notificaciones_no_leidas'] = persona.notificacion_set.filter(leida=False)
            except:
                pass
        
        # Notificaciones del superusuario
        if request.user.is_superuser:
            context['notificaciones_superusuario_no_leidas'] = NotificacionSuperusuario.objects.filter(leida=False)
    
    return context

