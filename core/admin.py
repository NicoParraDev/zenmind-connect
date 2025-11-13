"""
Configuración del panel de administración de Django.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Tipousuario, Especialidad, Persona, Psicologo, Horarios, 
    Agenda, HorarioAgenda, Post, Hilo, Comment, Notificacion, NotificacionSuperusuario,
    ChatConversation, ChatMessageBot, GrupoApoyo, MiembroGrupo, SesionGrupo, RecursoGrupo
)


@admin.register(Tipousuario)
class TipousuarioAdmin(admin.ModelAdmin):
    """Administración de tipos de usuario."""
    list_display = ('idTipoUsuario', 'tipoUsuario')
    search_fields = ('tipoUsuario',)
    list_filter = ('tipoUsuario',)


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    """Administración de especialidades."""
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(Psicologo)
class PsicologoAdmin(admin.ModelAdmin):
    """Administración de psicólogos."""
    list_display = ('id', 'nombre', 'rut', 'email', 'telefono', 'especialidad')
    list_filter = ('especialidad',)
    search_fields = ('nombre', 'rut', 'email')
    readonly_fields = ('id',)


@admin.register(Horarios)
class HorariosAdmin(admin.ModelAdmin):
    """Administración de horarios."""
    list_display = ('id', 'horas')
    search_fields = ('horas',)


@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    """Administración de agendas."""
    list_display = ('id', 'psicologo', 'data', 'mostrar_horarios', 'horarios_disponibles', 'horarios_reservados')
    list_filter = ('data', 'psicologo')
    search_fields = ('psicologo__nombre',)
    filter_horizontal = ('horarios',)
    date_hierarchy = 'data'
    
    def mostrar_horarios(self, obj):
        """Muestra los horarios de la agenda."""
        return ", ".join([h.horas for h in obj.horarios.all()])
    mostrar_horarios.short_description = 'Horarios'
    
    def horarios_disponibles(self, obj):
        """Muestra la cantidad de horarios disponibles."""
        return obj.get_horarios_disponibles().count()
    horarios_disponibles.short_description = 'Disponibles'
    
    def horarios_reservados(self, obj):
        """Muestra la cantidad de horarios reservados."""
        return obj.get_horarios_reservados().count()
    horarios_reservados.short_description = 'Reservados'


@admin.register(HorarioAgenda)
class HorarioAgendaAdmin(admin.ModelAdmin):
    """Administración de horarios de agenda."""
    list_display = ('id', 'agenda', 'horario', 'reservado_por', 'esta_disponible', 'fecha_reserva')
    list_filter = ('agenda__psicologo', 'agenda__data', 'reservado_por', 'fecha_reserva')
    search_fields = ('agenda__psicologo__nombre', 'horario__horas', 'reservado_por__nombre', 'reservado_por__apellido')
    readonly_fields = ('fecha_reserva',)
    date_hierarchy = 'fecha_reserva'
    
    def esta_disponible(self, obj):
        """Indica si el horario está disponible."""
        return obj.esta_disponible
    esta_disponible.boolean = True
    esta_disponible.short_description = 'Disponible'


@admin.register(Hilo)
class HiloAdmin(admin.ModelAdmin):
    """Administración de hilos/temas."""
    list_display = ('idTiphilo', 'nombreHilo')
    search_fields = ('nombreHilo',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Administración de posts."""
    list_display = ('idPost', 'title', 'author', 'hilo', 'date_added', 'slug')
    list_filter = ('date_added', 'hilo', 'author')
    search_fields = ('title', 'intro', 'body', 'author__nombre')
    readonly_fields = ('date_added', 'slug')
    date_hierarchy = 'date_added'
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    """Administración de personas/usuarios."""
    list_display = ('rut', 'nombre', 'apellido', 'correo', 'telefono', 'tipousuario', 'user')
    list_filter = ('tipousuario', 'fechaNac')
    search_fields = ('rut', 'nombre', 'apellido', 'correo', 'telefono')
    readonly_fields = ('rut',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Administración de comentarios."""
    list_display = ('id', 'name', 'post', 'author', 'date_added', 'preview_body')
    list_filter = ('date_added', 'post')
    search_fields = ('name', 'body', 'post__title', 'author__nombre')
    readonly_fields = ('date_added',)
    date_hierarchy = 'date_added'
    
    def preview_body(self, obj):
        """Muestra una vista previa del cuerpo del comentario."""
        return obj.body[:50] + "..." if len(obj.body) > 50 else obj.body
    preview_body.short_description = 'Vista Previa'


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    """Administración de notificaciones."""
    list_display = ('id', 'persona', 'contenido_preview', 'leida', 'comentario')
    list_filter = ('leida', 'persona')
    search_fields = ('contenido', 'persona__nombre')
    readonly_fields = ('id',)
    
    def contenido_preview(self, obj):
        """Muestra una vista previa del contenido."""
        return obj.contenido[:50] + "..." if len(obj.contenido) > 50 else obj.contenido
    contenido_preview.short_description = 'Contenido'


@admin.register(NotificacionSuperusuario)
class NotificacionSuperusuarioAdmin(admin.ModelAdmin):
    """Administración de notificaciones de superusuario."""
    list_display = ('id', 'contenido_preview', 'leida', 'comentario')
    list_filter = ('leida',)
    search_fields = ('contenido',)
    readonly_fields = ('id',)
    
    def contenido_preview(self, obj):
        """Muestra una vista previa del contenido."""
        return obj.contenido[:50] + "..." if len(obj.contenido) > 50 else obj.contenido
    contenido_preview.short_description = 'Contenido'


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    """Administración de conversaciones del chatbot."""
    list_display = ('id', 'persona', 'created_at', 'updated_at', 'is_active', 'message_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('persona__nombre', 'persona__apellido', 'persona__correo')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def message_count(self, obj):
        """Muestra el número de mensajes."""
        return obj.get_message_count()
    message_count.short_description = 'Mensajes'


@admin.register(ChatMessageBot)
class ChatMessageBotAdmin(admin.ModelAdmin):
    """Administración de mensajes del chatbot."""
    list_display = ('id', 'conversation', 'role', 'message_preview', 'is_crisis_detected', 'created_at')
    list_filter = ('role', 'is_crisis_detected', 'created_at')
    search_fields = ('message', 'conversation__persona__nombre')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def message_preview(self, obj):
        """Muestra una vista previa del mensaje."""
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Mensaje'


@admin.register(GrupoApoyo)
class GrupoApoyoAdmin(admin.ModelAdmin):
    """Administración de grupos de apoyo."""
    list_display = ('id', 'nombre', 'tema', 'creado_por', 'get_miembro_count', 'max_miembros', 'is_activo', 'created_at')
    list_filter = ('tema', 'is_activo', 'is_publico', 'created_at')
    search_fields = ('nombre', 'descripcion', 'creado_por__nombre')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(MiembroGrupo)
class MiembroGrupoAdmin(admin.ModelAdmin):
    """Administración de miembros de grupos."""
    list_display = ('id', 'grupo', 'persona', 'fecha_union', 'is_activo', 'es_moderador')
    list_filter = ('is_activo', 'es_moderador', 'fecha_union')
    search_fields = ('grupo__nombre', 'persona__nombre', 'persona__apellido')
    date_hierarchy = 'fecha_union'


@admin.register(SesionGrupo)
class SesionGrupoAdmin(admin.ModelAdmin):
    """Administración de sesiones grupales."""
    list_display = ('id', 'grupo', 'fecha_programada', 'psicologo_facilitador', 'is_activa')
    list_filter = ('is_activa', 'fecha_programada')
    search_fields = ('grupo__nombre', 'tema_sesion')
    date_hierarchy = 'fecha_programada'


@admin.register(RecursoGrupo)
class RecursoGrupoAdmin(admin.ModelAdmin):
    """Administración de recursos de grupos."""
    list_display = ('id', 'titulo', 'grupo', 'tipo', 'compartido_por', 'created_at')
    list_filter = ('tipo', 'created_at')
    search_fields = ('titulo', 'descripcion', 'grupo__nombre')
    date_hierarchy = 'created_at'
