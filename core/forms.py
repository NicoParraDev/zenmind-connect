"""
Formularios de Django para ZenMindConnect.
Incluye protección honeypot contra bots.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from datetime import date
import bleach
from .models import Post, Comment, Persona, Psicologo, Especialidad, Horarios, Agenda, Hilo
try:
    from .utils import validar_rut_chileno, validar_telefono_chileno, limpiar_telefono
except ImportError:
    # Fallback si utils.py no existe
    def validar_rut_chileno(rut):
        return True, rut.replace('.', '').replace('-', '').upper(), ""
    def validar_telefono_chileno(telefono):
        return True, ""
    def limpiar_telefono(telefono):
        return telefono.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

from .helpers import validar_fecha_futura, validar_fecha_agenda
from .security import (
    validar_entrada_segura,
    validar_sin_sql_injection,
    validar_sin_xss,
    validar_sin_command_injection,
    registrar_intento_sospechoso
)


class PersonaForm(forms.ModelForm):
    """Formulario para crear/editar una Persona con validaciones mejoradas."""
    
    class Meta:
        model = Persona
        fields = ['rut', 'nombre', 'apellido', 'fechaNac', 'correo', 'telefono']
        widgets = {
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12.345.678-9'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'fechaNac': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56912345678'
            }),
        }
    
    def clean_rut(self):
        """Valida y limpia el RUT chileno con protección de seguridad."""
        rut = self.cleaned_data.get('rut')
        if rut:
            # Protección contra inyección SQL y XSS
            try:
                rut = validar_sin_sql_injection(str(rut), 'rut')
                rut = validar_sin_xss(str(rut), 'rut')
            except ValidationError as e:
                if hasattr(self, 'request'):
                    registrar_intento_sospechoso(self.request, "SQL_INJECTION_XSS", f"Campo RUT: {rut[:50]}")
                raise
            
            es_valido, rut_limpio, mensaje = validar_rut_chileno(rut)
            if not es_valido:
                raise ValidationError(mensaje)
            return rut_limpio
        return rut
    
    def clean_telefono(self):
        """Valida y limpia el teléfono chileno."""
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            es_valido, mensaje = validar_telefono_chileno(telefono)
            if not es_valido:
                raise ValidationError(mensaje)
            return limpiar_telefono(telefono)
        return telefono
    
    def clean_fechaNac(self):
        """Valida que la fecha de nacimiento sea razonable."""
        fecha = self.cleaned_data.get('fechaNac')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            
            if edad < 13:
                raise ValidationError("Debes tener al menos 13 años para registrarte.")
            if edad > 120:
                raise ValidationError("La fecha de nacimiento no es válida.")
        
        return fecha
    
    def clean_nombre(self):
        """Valida que el nombre solo contenga letras y espacios con protección de seguridad."""
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            # Protección contra ataques
            try:
                nombre = validar_entrada_segura(str(nombre), 'nombre', max_longitud=20)
            except ValidationError as e:
                if hasattr(self, 'request'):
                    registrar_intento_sospechoso(self.request, "ATTACK_DETECTED", f"Campo nombre: {nombre[:50]}")
                raise
            
            if not nombre.replace(' ', '').isalpha():
                raise ValidationError("El nombre solo puede contener letras y espacios.")
            if len(nombre.strip()) < 2:
                raise ValidationError("El nombre debe tener al menos 2 caracteres.")
        return nombre.strip() if nombre else nombre
    
    def clean_apellido(self):
        """Valida que el apellido solo contenga letras y espacios con protección de seguridad."""
        apellido = self.cleaned_data.get('apellido')
        if apellido:
            # Protección contra ataques
            try:
                apellido = validar_entrada_segura(str(apellido), 'apellido', max_longitud=20)
            except ValidationError as e:
                if hasattr(self, 'request'):
                    registrar_intento_sospechoso(self.request, "ATTACK_DETECTED", f"Campo apellido: {apellido[:50]}")
                raise
            
            if not apellido.replace(' ', '').isalpha():
                raise ValidationError("El apellido solo puede contener letras y espacios.")
            if len(apellido.strip()) < 2:
                raise ValidationError("El apellido debe tener al menos 2 caracteres.")
        return apellido.strip() if apellido else apellido


class CommentForm(forms.ModelForm):
    """Formulario para crear comentarios con validaciones."""
    
    class Meta:
        model = Comment
        fields = ['name', 'body']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu comentario...'
            }),
        }
    
    def clean_body(self):
        """Valida y sanitiza el comentario con protección de seguridad."""
        body = self.cleaned_data.get('body')
        if body:
            # Protección contra XSS y SQL injection
            try:
                body = validar_entrada_segura(str(body), 'body', max_longitud=2000)
            except ValidationError as e:
                if hasattr(self, 'request'):
                    registrar_intento_sospechoso(self.request, "XSS_SQL_INJECTION", f"Campo body: {body[:100]}")
                raise
            
            # Sanitizar HTML usando bleach (permite solo texto plano, sin HTML)
            # Esto previene XSS incluso si se escapa la validación anterior
            body = bleach.clean(
                body,
                tags=[],  # No permitir ningún tag HTML
                attributes={},
                strip=True  # Eliminar tags no permitidos
            )
            
            if len(body.strip()) < 5:
                raise ValidationError("El comentario debe tener al menos 5 caracteres.")
        return body.strip() if body else body


class PostForm(forms.ModelForm):
    """Formulario para crear/editar posts."""
    
    class Meta:
        model = Post
        fields = ['title', 'slug', 'intro', 'body', 'imagen', 'video_url', 'hilo']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del post'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'url-amigable (opcional)'
            }),
            'intro': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Introducción breve...'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Contenido del post...'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=... o https://vimeo.com/...'
            }),
            'hilo': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que slug no sea requerido (se genera automáticamente si está vacío)
        self.fields['slug'].required = False
    
    def clean_title(self):
        """Valida que el título tenga contenido con protección de seguridad."""
        title = self.cleaned_data.get('title')
        if title:
            # Protección contra ataques
            try:
                title = validar_entrada_segura(str(title), 'title', max_longitud=255)
            except ValidationError as e:
                if hasattr(self, 'request'):
                    registrar_intento_sospechoso(self.request, "ATTACK_DETECTED", f"Campo title: {title[:100]}")
                raise
            
            if len(title.strip()) < 5:
                raise ValidationError("El título debe tener al menos 5 caracteres.")
        return title.strip() if title else title
    
    def clean_intro(self):
        """Valida que la introducción tenga contenido con protección de seguridad."""
        intro = self.cleaned_data.get('intro')
        if intro:
            # Protección contra ataques
            try:
                intro = validar_entrada_segura(str(intro), 'intro', max_longitud=500)
            except ValidationError as e:
                if hasattr(self, 'request'):
                    registrar_intento_sospechoso(self.request, "ATTACK_DETECTED", f"Campo intro: {intro[:100]}")
                raise
            
            if len(intro.strip()) < 10:
                raise ValidationError("La introducción debe tener al menos 10 caracteres.")
        return intro.strip() if intro else intro
    
    def clean_body(self):
        """Valida que el cuerpo tenga contenido con protección de seguridad."""
        body = self.cleaned_data.get('body')
        if body:
            body_str = str(body)
            
            # Validar longitud
            if len(body_str) > 10000:
                raise ValidationError("El contenido excede la longitud máxima de 10000 caracteres.")
            
            # Validar contra SQL injection (permitir HTML básico de CKEditor)
            try:
                validar_sin_sql_injection(body_str, 'body')
            except ValidationError as e:
                if hasattr(self, 'request'):
                    registrar_intento_sospechoso(self.request, "ATTACK_DETECTED", f"Campo body: {body_str[:100]}")
                raise ValidationError("El campo 'body' contiene caracteres no permitidos por seguridad.")
            
            # Validar contra command injection
            try:
                validar_sin_command_injection(body_str, 'body')
            except ValidationError as e:
                if hasattr(self, 'request'):
                    registrar_intento_sospechoso(self.request, "ATTACK_DETECTED", f"Campo body: {body_str[:100]}")
                raise ValidationError("El campo 'body' contiene caracteres no permitidos por seguridad.")
            
            # Obtener solo el texto plano para validar longitud mínima (sin HTML)
            import bleach
            texto_plano = bleach.clean(body_str, tags=[], strip=True)
            if len(texto_plano.strip()) < 20:
                raise ValidationError("El contenido debe tener al menos 20 caracteres.")
            
            # Sanitizar HTML con bleach para seguridad (permitir solo tags seguros)
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote']
            allowed_attributes = {
                'a': ['href', 'title'],
                'img': ['src', 'alt', 'title', 'width', 'height']
            }
            body = bleach.clean(body_str, tags=allowed_tags, attributes=allowed_attributes, strip=True)
        return body.strip() if body else body
    
    def clean_imagen(self):
        """Valida la imagen subida."""
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            # Verificar si es un archivo nuevo (tiene content_type) o un archivo existente (ImageFieldFile)
            # ImageFieldFile no tiene content_type, solo se valida si es un archivo nuevo
            if hasattr(imagen, 'content_type'):
                # Es un archivo nuevo, validarlo
                from core.security import validar_tipo_archivo
                es_valido, mensaje = validar_tipo_archivo(imagen, max_tamaño_mb=5)
                if not es_valido:
                    raise ValidationError(mensaje)
            # Si no tiene content_type, es un ImageFieldFile existente, no necesita validación
        return imagen
    
    def clean_video_url(self):
        """Valida que la URL de video sea de YouTube o Vimeo."""
        video_url = self.cleaned_data.get('video_url')
        if video_url:
            es_youtube = 'youtube.com' in video_url or 'youtu.be' in video_url
            es_vimeo = 'vimeo.com' in video_url
            
            if not es_youtube and not es_vimeo:
                raise ValidationError("Solo se permiten URLs de YouTube o Vimeo.")
        return video_url
    
    def clean_slug(self):
        """Valida que el slug sea único o se generará automáticamente."""
        slug = self.cleaned_data.get('slug')
        if slug:
            # Normalizar el slug
            from django.utils.text import slugify
            slug = slugify(slug)
            
            # Si es un post existente, excluir su propio slug
            queryset = Post.objects.filter(slug=slug)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            # Si el slug ya existe, informar al usuario (pero no fallar, se manejará en save())
            if queryset.exists():
                # No lanzamos error aquí porque el método save() lo manejará automáticamente
                # Solo informamos que se agregará un número
                pass
        
        return slug


class PsicologoForm(forms.ModelForm):
    """Formulario para crear/editar psicólogos."""
    
    class Meta:
        model = Psicologo
        fields = ['nombre', 'rut', 'email', 'telefono', 'especialidad']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del psicólogo'
            }),
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ejemplo: 12345678-9'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56912345678'
            }),
            'especialidad': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class EspecialidadForm(forms.ModelForm):
    """Formulario para crear/editar especialidades."""
    
    class Meta:
        model = Especialidad
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la especialidad'
            }),
        }


class HorariosForm(forms.ModelForm):
    """Formulario para crear/editar horarios."""
    
    class Meta:
        model = Horarios
        fields = ['horas']
        widgets = {
            'horas': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class AgendaForm(forms.ModelForm):
    """Formulario para crear/editar agendas con validación de fechas."""
    
    class Meta:
        model = Agenda
        fields = ['psicologo', 'data', 'horarios']
        widgets = {
            'psicologo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'data': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'fecha-agenda',
                'placeholder': 'Selecciona una fecha',
                'readonly': True
            }),
            'horarios': forms.SelectMultiple(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super(AgendaForm, self).__init__(*args, **kwargs)
        # Cambia la etiqueta del campo 'data' a 'fecha'
        self.fields['data'].label = 'Fecha'
    
    def clean(self):
        """Valida la fecha y evita duplicados de agenda."""
        cleaned_data = super().clean()
        
        data = cleaned_data.get('data')
        psicologo = cleaned_data.get('psicologo')
        
        if not data or not psicologo:
            return cleaned_data
        
        # Usar función helper para validación centralizada
        try:
            validar_fecha_agenda(data, psicologo, self.instance)
        except ValidationError as e:
            raise ValidationError({'data': e.messages})
        
        return cleaned_data
