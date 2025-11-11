# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from .AI import predecir_sentimiento
# Procesamiento de comentario usando señales


# En models.py
class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, blank=False)

    class Meta:
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Psicologo(models.Model):
    nombre = models.CharField(max_length=200, blank=False, null=False)
    rut = models.CharField(max_length=30, blank=False, null=False, unique=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=17)
    especialidad = models.ForeignKey(Especialidad, on_delete= models.CASCADE, verbose_name='Especialidad',blank=False)

    class Meta:
        verbose_name = 'Psicólogo'
        verbose_name_plural = 'Psicólogos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Horarios(models.Model):
    HORA_CHOISES = (
        ('08:00AM⛅','08:00AM⛅'),
        ('09:00AM⛅','09:00AM⛅'),
        ('10:00AM⛅','10:00AM⛅'),
        ('11:00AM⛅','11:00AM⛅'),
        ('12:00PM☀️','12:00PM☀️'),
        ('13:00PM☀️','13:00PM☀️'),
        ('14:00PM☀️','14:00PM☀️'),
        ('15:00PM☀️','15:00PM☀️'),
        ('16:00PM☀️','16:00PM☀️'),
        ('17:00PM🌄','17:00PM🌄'),
        ('18:00PM🌄','18:00PM🌄'),
        ('19:00PM🌄','19:00PM🌄')
        
    )
    horas = models.CharField(max_length=9,choices=HORA_CHOISES, blank=False, null=False)

    def __str__(self):
        return self.horas

class Agenda(models.Model):
    psicologo = models.ForeignKey(Psicologo, on_delete=models.CASCADE, verbose_name='Psicologo Especialista',blank=False)
    data = models.DateField(db_index=True)
    horarios = models.ManyToManyField(Horarios, blank= False, through='HorarioAgenda')

    def __str__(self):
        return str(self.psicologo.nombre)
    
    def get_horarios_disponibles(self):
        """Retorna los horarios disponibles (no reservados) de esta agenda."""
        return self.horarioagenda_set.filter(reservado_por__isnull=True)
    
    def get_horarios_reservados(self):
        """Retorna los horarios reservados de esta agenda."""
        return self.horarioagenda_set.filter(reservado_por__isnull=False)


class HorarioAgenda(models.Model):
    """
    Modelo intermedio que relaciona Agenda, Horario y Persona.
    Permite saber qué horario específico fue reservado por qué paciente.
    """
    agenda = models.ForeignKey(Agenda, on_delete=models.CASCADE)
    horario = models.ForeignKey(Horarios, on_delete=models.CASCADE)
    reservado_por = models.ForeignKey('Persona', on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    fecha_reserva = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        unique_together = ('agenda', 'horario')  # Un horario solo puede aparecer una vez por agenda
        verbose_name = 'Horario de Agenda'
        verbose_name_plural = 'Horarios de Agenda'
    
    def __str__(self):
        estado = "Reservado" if self.reservado_por else "Disponible"
        return f"{self.agenda.psicologo.nombre} - {self.horario.horas} ({estado})"
    
    @property
    def esta_disponible(self):
        """Retorna True si el horario está disponible."""
        return self.reservado_por is None


class Hilo(models.Model):
    idTiphilo = models.AutoField(primary_key=True, verbose_name='Id Hilo', unique=True)
    nombreHilo = models.CharField(max_length=50, verbose_name='Nombre hilo')

    def __str__(self):
        return self.nombreHilo




class Tipousuario(models.Model):
    """Modelo para tipos de usuario del sistema."""
    # Constantes para tipos de usuario
    TIPO_ADMIN = 1
    TIPO_REGULAR = 2
    
    idTipoUsuario = models.AutoField(primary_key=True, verbose_name='Id_tipo_usuario', unique=True)
    tipoUsuario = models.CharField(max_length=50, verbose_name='Tipo_usuario')

    class Meta:
        verbose_name = 'Tipo de Usuario'
        verbose_name_plural = 'Tipos de Usuario'
        ordering = ['idTipoUsuario']

    def __str__(self):
        return self.tipoUsuario







class Persona(models.Model):
    rut = models.CharField(max_length=12, primary_key=True, verbose_name='Rut_usuario', unique=True, db_index=True)
    nombre = models.CharField(max_length=20, verbose_name='Nombre_usuario', db_index=True)
    apellido = models.CharField(max_length=20, verbose_name='Apellido_usuario', db_index=True)
    fechaNac = models.DateField(max_length=10, verbose_name='Nacimiento_usuario')
    correo = models.EmailField(max_length=50, verbose_name='Correo_usuario', unique=True, db_index=True)
    telefono = models.CharField(max_length=12, verbose_name='telefono_psicologo', unique=True, db_index=True)
    contrasena = models.CharField(max_length=36, verbose_name='Contrasena_usuario')
    tipousuario = models.ForeignKey(Tipousuario, on_delete=models.CASCADE, db_index=True)
    consulta = models.ManyToManyField(Agenda, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_index=True)

    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        ordering = ['apellido', 'nombre']
        indexes = [
            models.Index(fields=['apellido', 'nombre']),
            models.Index(fields=['correo']),
            models.Index(fields=['tipousuario']),
        ]

    def __str__(self):
        return self.rut





class Post(models.Model):
    idPost = models.AutoField(primary_key=True, verbose_name='Id Post', unique=True)
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True, max_length=50, db_index=True)  # Define la longitud máxima
    intro = models.TextField()
    body = models.TextField()
    imagen = models.ImageField(upload_to='posts/', blank=True, null=True, verbose_name='Imagen del post')
    video_url = models.URLField(blank=True, null=True, max_length=500, verbose_name='URL de video (YouTube/Vimeo)')
    hilo = models.ForeignKey(Hilo, on_delete=models.CASCADE, db_index=True)
    date_added = models.DateTimeField(auto_now_add=True, db_index=True)
    author = models.ForeignKey(Persona, on_delete=models.CASCADE, db_index=True)
    reportado = models.BooleanField(default=False, verbose_name='Reportado por contenido inapropiado')
    moderado = models.BooleanField(default=False, verbose_name='Moderado')

    class Meta:
        ordering = ['-date_added']
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        indexes = [
            models.Index(fields=['-date_added', 'hilo']),
            models.Index(fields=['author', '-date_added']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Retorna la URL canónica del post."""
        from django.urls import reverse
        return reverse('post_detail', kwargs={'slug': self.slug})
    
    def get_comment_count(self):
        """Retorna el número de comentarios del post."""
        return self.comments.count()
    
    def get_preview(self, length=100):
        """Retorna una vista previa del contenido."""
        if len(self.intro) > length:
            return self.intro[:length] + "..."
        return self.intro

    def save(self, *args, **kwargs):
        # Generar un slug único basado en el título si no existe
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Normalizar el slug (eliminar espacios y caracteres especiales)
        self.slug = slugify(self.slug) if self.slug else slugify(self.title)

        # Verificar si el slug ya existe y agregar un sufijo numérico si es necesario
        original_slug = self.slug
        count = 1
        
        # Si es un post existente, excluir su propio slug de la verificación
        queryset = Post.objects.filter(slug=self.slug)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        
        # Buscar un slug único agregando sufijo numérico si es necesario
        while queryset.exists():
            self.slug = f"{original_slug}-{count}"
            queryset = Post.objects.filter(slug=self.slug)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            count += 1
            
            # Protección contra bucles infinitos (máximo 1000 intentos)
            if count > 1000:
                # Si llegamos aquí, usar timestamp como último recurso
                import time
                self.slug = f"{original_slug}-{int(time.time())}"
                break

        # Asegurarse de que el slug no supere la longitud máxima
        max_length = self._meta.get_field('slug').max_length
        if len(self.slug) > max_length:
            # Truncar y agregar sufijo si es necesario
            truncated = self.slug[:max_length-3]
            if not Post.objects.filter(slug=truncated).exists():
                self.slug = truncated
            else:
                # Si el truncado también existe, usar timestamp
                import time
                self.slug = f"{truncated[:max_length-15]}-{int(time.time())}"[:max_length]

        super().save(*args, **kwargs)
    
    def get_youtube_video_id(self):
        """Extrae el ID del video de YouTube desde la URL."""
        if not self.video_url:
            return None
        
        import re
        # Patrón para diferentes formatos de URL de YouTube
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.video_url)
            if match:
                return match.group(1)
        
        return None
    
    def get_vimeo_video_id(self):
        """Extrae el ID del video de Vimeo desde la URL."""
        if not self.video_url:
            return None
        
        import re
        # Patrón para URL de Vimeo
        pattern = r'vimeo\.com\/(\d+)'
        match = re.search(pattern, self.video_url)
        if match:
            return match.group(1)
        
        return None
    
    def get_video_embed_url(self):
        """Retorna la URL de embed del video (YouTube o Vimeo)."""
        if not self.video_url:
            return None
        
        youtube_id = self.get_youtube_video_id()
        if youtube_id:
            return f"https://www.youtube.com/embed/{youtube_id}"
        
        vimeo_id = self.get_vimeo_video_id()
        if vimeo_id:
            return f"https://player.vimeo.com/video/{vimeo_id}"
        
        return None




class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE, db_index=True)
    name = models.CharField(max_length=255)
    body = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True, db_index=True)
    author = models.ForeignKey(Persona, on_delete=models.CASCADE, null=True, db_index=True)
    reportado = models.BooleanField(default=False, verbose_name='Reportado por contenido inapropiado')

    class Meta:
        ordering = ['date_added']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        indexes = [
            models.Index(fields=['post', 'date_added']),
            models.Index(fields=['author', 'date_added']),
        ]

    def __str__(self):
        return f"Comentario de {self.name} en {self.post.title}"
    
    def get_author_name(self):
        """Retorna el nombre del autor del comentario."""
        if self.author:
            return f"{self.author.nombre} {self.author.apellido}"
        return self.name



class Notificacion(models.Model):
    contenido = models.TextField()
    comentario = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, related_name='notificaciones', db_index=True)
    leida = models.BooleanField(default=False, db_index=True)
    persona = models.ForeignKey('Persona', on_delete=models.CASCADE, db_index=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True, null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['persona', '-fecha', 'leida']),
        ]

    def __str__(self):
        return self.contenido



class NotificacionSuperusuario(models.Model):
    contenido = models.TextField()
    comentario = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, related_name='notificaciones_superusuario')
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Notificación Superusuario'
        verbose_name_plural = 'Notificaciones Superusuario'

    def __str__(self):
        return self.contenido



@receiver(post_save, sender=Comment)
def procesar_comentario_signal(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de guardar un comentario.
    Analiza el sentimiento y crea notificaciones si es necesario.
    """
    import logging
    from .comment_processing import procesar_comentario
    
    logger = logging.getLogger(__name__)
    
    # Solo procesar si es un nuevo comentario (no actualización)
    if not created:
        logger.debug(f"Comentario {instance.id} no es nuevo, saltando procesamiento")
        return
    
    logger.info(f"=== SIGNAL EJECUTADO === Comentario ID: {instance.id} creado")
    logger.info(f"Contenido del comentario: '{instance.body}'")
    
    try:
        comentario = instance
        sentimiento_predicho = procesar_comentario(comentario)
        
        logger.info(f"Sentimiento predicho por signal: {sentimiento_predicho}")

        # Acciones basadas en el sentimiento predicho
        if sentimiento_predicho == 'negativo':
            logger.info("=== COMENTARIO NEGATIVO DETECTADO ===")
            
            # Notificar al superusuario de Django
            superusuario_django = User.objects.filter(is_superuser=True).first()
            
            if not superusuario_django:
                logger.warning("No se encontró ningún superusuario para notificar")
                return
            
            logger.info(f"Superusuario encontrado: {superusuario_django.username}")
            
            try:
                # Obtener información del autor del comentario
                autor_nombre = 'Usuario desconocido'
                post_autor = 'Post desconocido'
                
                if comentario.author and comentario.author.user:
                    autor_nombre = comentario.author.user.username
                elif comentario.name:
                    autor_nombre = comentario.name
                
                if comentario.post:
                    if comentario.post.author:
                        post_autor = comentario.post.author.nombre if hasattr(comentario.post.author, 'nombre') else comentario.post.author.user.username if comentario.post.author.user else 'Desconocido'
                    post_titulo = comentario.post.title
                else:
                    post_titulo = 'Sin post'
                
                # Crear notificación con más información
                contenido_notificacion = (
                    f"Comentario <span style='color: red; font-weight: bold;'>negativo</span> detectado<br>"
                    f"<strong>Post:</strong> {post_titulo}<br>"
                    f"<strong>Autor del comentario:</strong> {autor_nombre}<br>"
                    f"<strong>Comentario:</strong> {comentario.body[:100]}{'...' if len(comentario.body) > 100 else ''}"
                )
                
                notificacion = NotificacionSuperusuario.objects.create(
                    contenido=contenido_notificacion,
                    comentario=comentario
                )
                
                logger.info(f"NOTIFICACION CREADA EXITOSAMENTE - ID: {notificacion.id}")
                logger.info(f"Contenido: {contenido_notificacion}")
                
            except Exception as e:
                logger.error(f"ERROR al crear notificación de superusuario: {e}", exc_info=True)
                import traceback
                logger.error(f"Traceback completo: {traceback.format_exc()}")
        else:
            logger.info(f"Comentario no es negativo (sentimiento: {sentimiento_predicho}), no se crea notificación")
            
    except Exception as e:
        logger.error(f"ERROR CRITICO en señal procesar_comentario: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")       


# ============================================
# MODELOS DE VIDEOCALL Y CHAT
# ============================================

class VideoCallRoom(models.Model):
    """
    Sala de videollamada integrada con sistema de reservas.
    """
    ROOM_TYPE_CHOICES = [
        ('private', 'Sesión Privada'),
        ('group', 'Evento Grupal'),
    ]
    
    name = models.CharField(max_length=200, unique=True, db_index=True, verbose_name='Nombre de sala')
    created_by = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='salas_creadas', verbose_name='Creado por')
    agenda = models.ForeignKey(Agenda, on_delete=models.SET_NULL, null=True, blank=True, related_name='salas_videocall', verbose_name='Agenda asociada')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Fecha de creación')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='Activa')
    room_type = models.CharField(
        max_length=20, 
        choices=ROOM_TYPE_CHOICES, 
        default='private',
        db_index=True,
        verbose_name='Tipo de sala',
        help_text='Sesión Privada: psicólogo + practicante + paciente(s). Evento Grupal: psicólogo + muchos usuarios'
    )
    is_couple_therapy = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Terapia de pareja',
        help_text='Si está activado, permite hasta 5 participantes (psicólogo + practicante + pareja)'
    )
    max_participants = models.IntegerField(
        default=3,
        verbose_name='Máximo de participantes',
        help_text='Sesión privada: 3-5 participantes. Evento grupal: hasta 50 participantes'
    )
    
    class Meta:
        verbose_name = 'Sala de Videollamada'
        verbose_name_plural = 'Salas de Videollamada'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['created_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.created_by}"
    
    def get_member_count(self):
        """Retorna el número de miembros activos en la sala."""
        return self.members.filter(insession=True).count()


class RoomMember(models.Model):
    """
    Miembro en una sala de videollamada.
    """
    ROLE_CHOICES = [
        ('psicologo', 'Psicólogo'),
        ('practicante', 'Practicante'),
        ('paciente', 'Paciente'),
        ('audience', 'Audiencia'),
    ]
    
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='miembros_salas', verbose_name='Persona')
    room = models.ForeignKey(VideoCallRoom, on_delete=models.CASCADE, related_name='members', verbose_name='Sala')
    uid = models.CharField(max_length=1000, verbose_name='UID de Agora')
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='paciente',
        db_index=True,
        verbose_name='Rol',
        help_text='Rol del participante en la sala'
    )
    joined_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Fecha de ingreso')
    left_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de salida')
    insession = models.BooleanField(default=True, db_index=True, verbose_name='En sesión')
    
    class Meta:
        verbose_name = 'Miembro de Sala'
        verbose_name_plural = 'Miembros de Sala'
        ordering = ['-joined_at']
        unique_together = ('room', 'uid')
        indexes = [
            models.Index(fields=['room', 'insession']),
            models.Index(fields=['persona', '-joined_at']),
        ]
    
    def __str__(self):
        return f"{self.persona} en {self.room.name}"
    
    def leave_session(self):
        """Marca al miembro como fuera de sesión."""
        self.insession = False
        self.left_at = timezone.now()
        self.save()


class ChatMessage(models.Model):
    """
    Mensaje de chat en una sala de videollamada.
    """
    room = models.ForeignKey(VideoCallRoom, on_delete=models.CASCADE, related_name='chat_messages', verbose_name='Sala')
    author = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='mensajes_chat', verbose_name='Autor')
    message = models.TextField(max_length=5000, verbose_name='Mensaje')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Fecha de creación')
    
    class Meta:
        verbose_name = 'Mensaje de Chat'
        verbose_name_plural = 'Mensajes de Chat'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', 'created_at']),
            models.Index(fields=['author', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.author} en {self.room.name}: {self.message[:50]}"
    
    def get_author_name(self):
        """Retorna el nombre completo del autor."""
        return f"{self.author.nombre} {self.author.apellido}"


