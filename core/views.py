"""
Vistas de la aplicación core de ZenMindConnect.
Incluye todas las vistas principales del sistema.
"""
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, Http404, HttpRequest
from django.views.decorators.csrf import requires_csrf_token
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import (
    Persona, Post, Comment, Tipousuario, Notificacion, 
    NotificacionSuperusuario, Hilo
)
from .forms import PersonaForm, PostForm, CommentForm
from .decorators import rate_limit, get_client_ip
from .security import registrar_intento_sospechoso
from .helpers import validar_fecha_futura
from .comment_processing import procesar_comentario

logger = logging.getLogger(__name__)


# ============================================
# VISTAS BÁSICAS
# ============================================

def index(request: HttpRequest) -> HttpResponse:
    """
    Vista principal de la aplicación.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse: Renderiza la página principal
    """
    return render(request, 'core/index.html')


def nos(request: HttpRequest) -> HttpResponse:
    """
    Vista 'Nosotros'.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse: Renderiza la página 'Nosotros'
    """
    return render(request, 'core/nos.html')


def coming_son(request: HttpRequest) -> HttpResponse:
    """
    Vista 'Próximamente'.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse: Renderiza la página 'Próximamente'
    """
    return render(request, 'core/coming_son.html')


def log(request: HttpRequest) -> HttpResponse:
    """
    Vista de login.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse: Renderiza la página de login
    """
    return render(request, 'core/log.html')


# ============================================
# AUTENTICACIÓN
# ============================================

@rate_limit(max_attempts=5, window=300, key_prefix='login_rate_limit')
def login_view(request: HttpRequest) -> HttpResponse:
    """
    Vista de autenticación de usuario.
    
    Args:
        request: HttpRequest object con datos de login
        
    Returns:
        HttpResponse: Redirige según el resultado de la autenticación
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Validación básica
        if not username or not password:
            messages.error(request, 'Por favor, completa todos los campos.')
            return redirect('log')
        
        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            logger.info(f"Usuario {username} inició sesión exitosamente - IP: {get_client_ip(request)}")
            
            # Redirigir según tipo de usuario
            if user.is_superuser:
                return redirect('adm')
            else:
                try:
                    persona = Persona.objects.get(user=user)
                    return redirect('frontpage')
                except Persona.DoesNotExist:
                    messages.warning(request, 'Tu cuenta no tiene un perfil asociado.')
                    return redirect('form_persona')
        else:
            request.login_failed = True
            logger.warning(f"Intento de login fallido para usuario: {username} - IP: {get_client_ip(request)}")
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return redirect('log')
    
    return redirect('log')


def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Vista de logout.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse: Redirige al índice después de cerrar sesión
    """
    if request.user.is_authenticated:
        logger.info(f"Usuario {request.user.username} cerró sesión - IP: {get_client_ip(request)}")
        logout(request)
        messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('index')


# ============================================
# REGISTRO Y GESTIÓN DE USUARIOS
# ============================================

def registrar_usuario(request: HttpRequest) -> HttpResponse:
    """
    Vista para registrar un nuevo usuario.
    
    Args:
        request: HttpRequest object con datos del formulario
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después del registro
    """
    if request.method == 'POST':
        form = PersonaForm(request.POST)
        form.request = request  # Pasar request para logging de seguridad
        
        if form.is_valid():
            try:
                # Obtener datos del formulario
                rut = form.cleaned_data['rut']
                nombre = form.cleaned_data['nombre']
                apellido = form.cleaned_data['apellido']
                fecha_nac = form.cleaned_data['fechaNac']
                correo = form.cleaned_data['correo']
                telefono = form.cleaned_data['telefono']
                password = request.POST.get('contrasena', '')
                
                # Validar que no exista el usuario
                if Persona.objects.filter(rut=rut).exists():
                    messages.error(request, 'Este RUT ya está registrado.')
                    return render(request, 'core/form_persona.html', {'form': form})
                
                if Persona.objects.filter(correo=correo).exists():
                    messages.error(request, 'Este correo ya está registrado.')
                    return render(request, 'core/form_persona.html', {'form': form})
                
                # Obtener tipo de usuario regular
                tipo_regular = Tipousuario.objects.filter(tipoUsuario='Regular').first()
                if not tipo_regular:
                    tipo_regular = Tipousuario.objects.create(tipoUsuario='Regular')
                
                # Crear usuario de Django
                from django.contrib.auth.models import User
                username = correo.split('@')[0]  # Usar parte antes del @ como username
                # Asegurar username único
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=correo,
                    password=password
                )
                
                # Crear persona
                persona = Persona.objects.create(
                    rut=rut,
                    nombre=nombre,
                    apellido=apellido,
                    fechaNac=fecha_nac,
                    correo=correo,
                    telefono=telefono,
                    contrasena=password,  # En producción, esto debería ser hash
                    tipousuario=tipo_regular,
                    user=user
                )
                
                logger.info(f"Nuevo usuario registrado: {rut} - IP: {get_client_ip(request)}")
                messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
                return redirect('comprobante_registro', rut=rut)
                
            except Exception as e:
                logger.error(f"Error al registrar usuario: {e}", exc_info=True)
                messages.error(request, 'Ocurrió un error al registrar. Por favor, intenta nuevamente.')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = PersonaForm()
    
    return render(request, 'core/form_persona.html', {'form': form})


def comprobante_registro(request: HttpRequest, rut: str) -> HttpResponse:
    """
    Vista para mostrar comprobante de registro.
    
    Args:
        request: HttpRequest object
        rut: RUT del usuario registrado
        
    Returns:
        HttpResponse: Renderiza el comprobante de registro
    """
    try:
        persona = get_object_or_404(
            Persona.objects.select_related('tipousuario', 'user'),
            rut=rut
        )
        return render(request, 'core/comprobante_registro.html', {'persona': persona})
    except Exception as e:
        logger.error(f"Error al mostrar comprobante: {e}", exc_info=True)
        messages.error(request, 'Error al cargar el comprobante.')
        return redirect('index')


@login_required
def form_persona(request: HttpRequest) -> HttpResponse:
    """
    Vista para crear perfil de persona (requiere login).
    
    Args:
        request: HttpRequest object con datos del formulario
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de crear
    """
    if request.method == 'POST':
        form = PersonaForm(request.POST)
        form.request = request
        
        if form.is_valid():
            try:
                # Similar a registrar_usuario pero para usuarios ya autenticados
                rut = form.cleaned_data['rut']
                
                if Persona.objects.filter(rut=rut).exists():
                    messages.error(request, 'Este RUT ya está registrado.')
                    return render(request, 'core/form_persona.html', {'form': form})
                
                tipo_regular = Tipousuario.objects.filter(tipoUsuario='Regular').first()
                if not tipo_regular:
                    tipo_regular = Tipousuario.objects.create(tipoUsuario='Regular')
                
                persona = Persona.objects.create(
                    rut=rut,
                    nombre=form.cleaned_data['nombre'],
                    apellido=form.cleaned_data['apellido'],
                    fechaNac=form.cleaned_data['fechaNac'],
                    correo=form.cleaned_data['correo'],
                    telefono=form.cleaned_data['telefono'],
                    contrasena=request.user.password,
                    tipousuario=tipo_regular,
                    user=request.user
                )
                
                messages.success(request, 'Perfil creado exitosamente.')
                return redirect('frontpage')
                
            except Exception as e:
                logger.error(f"Error al crear perfil: {e}", exc_info=True)
                messages.error(request, 'Error al crear el perfil.')
        else:
            messages.error(request, 'Por favor, corrige los errores.')
    else:
        form = PersonaForm()
    
    return render(request, 'core/form_persona.html', {'form': form})


@login_required
def form_mod_persona(request: HttpRequest) -> HttpResponse:
    """
    Vista para modificar perfil de persona.
    
    Args:
        request: HttpRequest object con datos del formulario
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de actualizar
    """
    try:
        persona = Persona.objects.select_related('tipousuario', 'user').get(user=request.user)
    except Persona.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado.')
        return redirect('form_persona')
    
    if request.method == 'POST':
        form = PersonaForm(request.POST, instance=persona)
        form.request = request
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('area_de_persona', id=persona.rut)
            except Exception as e:
                logger.error(f"Error al actualizar perfil: {e}", exc_info=True)
                messages.error(request, 'Error al actualizar el perfil.')
        else:
            messages.error(request, 'Por favor, corrige los errores.')
    else:
        form = PersonaForm(instance=persona)
    
    return render(request, 'core/form_mod_persona.html', {'form': form, 'persona': persona})


@login_required
def form_borrar_persona(request: HttpRequest, id: str) -> HttpResponse:
    """
    Vista para eliminar perfil de persona.
    
    Args:
        request: HttpRequest object
        id: RUT de la persona a eliminar
        
    Returns:
        HttpResponse: Renderiza confirmación o redirige después de eliminar
    """
    try:
        persona = get_object_or_404(
            Persona.objects.select_related('tipousuario', 'user'),
            rut=id
        )
        
        # Verificar que el usuario sea el dueño
        if persona.user != request.user and not request.user.is_superuser:
            messages.error(request, 'No tienes permiso para realizar esta acción.')
            return redirect('index')
        
        if request.method == 'POST':
            persona.delete()
            messages.success(request, 'Perfil eliminado exitosamente.')
            return redirect('index')
        
        return render(request, 'core/form_borrar_persona.html', {'persona': persona})
        
    except Exception as e:
        logger.error(f"Error al eliminar perfil: {e}", exc_info=True)
        messages.error(request, 'Error al eliminar el perfil.')
        return redirect('index')


@login_required
def eliminar_cuenta_usuario(request: HttpRequest) -> HttpResponse:
    """
    Vista para eliminar cuenta de usuario completa.
    
    Args:
        request: HttpRequest object con POST para confirmar
        
    Returns:
        HttpResponse: Renderiza confirmación o redirige después de eliminar
    """
    if request.method == 'POST':
        try:
            if request.user.is_superuser:
                messages.error(request, 'No puedes eliminar una cuenta de administrador.')
                return redirect('index')
            
            # Eliminar persona asociada
            try:
                persona = Persona.objects.get(user=request.user)
                persona.delete()
            except Persona.DoesNotExist:
                pass
            
            # Eliminar usuario
            user = request.user
            logout(request)
            user.delete()
            
            messages.success(request, 'Tu cuenta ha sido eliminada exitosamente.')
            return redirect('index')
            
        except Exception as e:
            logger.error(f"Error al eliminar cuenta: {e}", exc_info=True)
            messages.error(request, 'Error al eliminar la cuenta.')
    
    return render(request, 'core/eliminar_cuenta_usuario.html')


@login_required
def lista_usuarios(request: HttpRequest) -> HttpResponse:
    """
    Vista para listar usuarios (solo superusuarios).
    
    Args:
        request: HttpRequest object (debe ser superusuario)
        
    Returns:
        HttpResponse: Renderiza la lista de usuarios con paginación
    """
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')
    
    usuarios = Persona.objects.select_related('tipousuario', 'user').all().order_by('apellido', 'nombre')
    
    # Paginación
    paginator = Paginator(usuarios, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/lista_usuarios.html', {'page_obj': page_obj})


# ============================================
# RECUPERACIÓN DE CONTRASEÑA
# ============================================

def forgetpassword(request: HttpRequest) -> HttpResponse:
    """
    Vista para solicitar recuperación de contraseña.
    
    Args:
        request: HttpRequest object con POST data ('username')
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de enviar email
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        
        if not username:
            messages.error(request, 'Por favor, ingresa tu nombre de usuario.')
            return render(request, 'core/forgetpassword.html')
        
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(username=username)
            
            # Generar token único
            token = secrets.token_urlsafe(32)
            
            # Guardar token en cache (válido por 1 hora)
            from django.core.cache import cache
            cache_key = f'password_reset_token_{token}'
            cache.set(cache_key, user.id, 3600)  # 1 hora
            
            # Obtener persona asociada
            try:
                persona = Persona.objects.get(user=user)
                user_rut = persona.rut
            except Persona.DoesNotExist:
                user_rut = user.username
            
            # Enviar email con enlace
            reset_url = request.build_absolute_uri(f'/changepassword/{token}/')
            
            try:
                send_mail(
                    subject='Recuperación de Contraseña - ZenMindConnect',
                    message=f'''
                    Hola {user.username},
                    
                    Has solicitado restablecer tu contraseña en ZenMindConnect.
                    
                    Haz clic en el siguiente enlace para restablecer tu contraseña:
                    {reset_url}
                    
                    Este enlace expirará en 1 hora.
                    
                    Si no solicitaste este cambio, ignora este mensaje.
                    
                    Saludos,
                    Equipo ZenMindConnect
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Se ha enviado un enlace de recuperación a tu correo electrónico.')
                return redirect('log')
                
            except Exception as e:
                logger.error(f"Error al enviar email de recuperación: {e}", exc_info=True)
                messages.error(request, 'Error al enviar el email. Por favor, contacta al administrador.')
        
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
        except Exception as e:
            logger.error(f"Error en forgetpassword: {e}", exc_info=True)
            messages.error(request, 'Ocurrió un error. Por favor, intenta nuevamente.')
    
    return render(request, 'core/forgetpassword.html')


def changepassword(request: HttpRequest, token: str) -> HttpResponse:
    """
    Vista para cambiar contraseña con token.
    
    Args:
        request: HttpRequest object con POST data ('new_password', 'reconfirm_password')
        token: Token de recuperación de contraseña
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de cambiar contraseña
    """
    # Validar token
    from django.core.cache import cache
    cache_key = f'password_reset_token_{token}'
    user_id = cache.get(cache_key)
    
    if not user_id:
        messages.error(request, 'El enlace de recuperación ha expirado o es inválido.')
        return redirect('forgetpassword')
    
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        
        try:
            persona = Persona.objects.get(user=user)
            user_rut = persona.rut
        except Persona.DoesNotExist:
            user_rut = user.username
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password', '')
            reconfirm_password = request.POST.get('reconfirm_password', '')
            
            if not new_password or not reconfirm_password:
                messages.error(request, 'Por favor, completa todos los campos.')
                return render(request, 'core/changepassword.html', {'user_rut': user_rut})
            
            if new_password != reconfirm_password:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'core/changepassword.html', {'user_rut': user_rut})
            
            if len(new_password) < 8:
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
                return render(request, 'core/changepassword.html', {'user_rut': user_rut})
            
            # Cambiar contraseña
            user.set_password(new_password)
            user.save()
            
            # Actualizar contraseña en Persona si existe
            try:
                persona = Persona.objects.get(user=user)
                persona.contrasena = new_password
                persona.save()
            except Persona.DoesNotExist:
                pass
            
            # Eliminar token
            cache.delete(cache_key)
            
            messages.success(request, 'Contraseña cambiada exitosamente. Ahora puedes iniciar sesión.')
            return redirect('log')
        
        return render(request, 'core/changepassword.html', {'user_rut': user_rut})
        
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('forgetpassword')
    except Exception as e:
        logger.error(f"Error en changepassword: {e}", exc_info=True)
        messages.error(request, 'Ocurrió un error. Por favor, intenta nuevamente.')
        return redirect('forgetpassword')


@login_required
def changepassword_login(request: HttpRequest) -> HttpResponse:
    """
    Vista para cambiar contraseña cuando el usuario está logueado.
    
    Args:
        request: HttpRequest object con POST data ('current_password', 'new_password', 'reconfirm_password')
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de cambiar contraseña
    """
    try:
        persona = Persona.objects.get(user=request.user)
        user_rut = persona.rut
    except Persona.DoesNotExist:
        user_rut = request.user.username
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        reconfirm_password = request.POST.get('reconfirm_password', '')
        
        # Validar contraseña actual
        if not request.user.check_password(current_password):
            messages.error(request, 'La contraseña actual es incorrecta.')
            return render(request, 'core/changepassword_login.html', {'user_rut': user_rut})
        
        # Validar nueva contraseña
        if not new_password or not reconfirm_password:
            messages.error(request, 'Por favor, completa todos los campos.')
            return render(request, 'core/changepassword_login.html', {'user_rut': user_rut})
        
        if new_password != reconfirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'core/changepassword_login.html', {'user_rut': user_rut})
        
        if len(new_password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return render(request, 'core/changepassword_login.html', {'user_rut': user_rut})
        
        # Cambiar contraseña
        request.user.set_password(new_password)
        request.user.save()
        
        # Actualizar en Persona
        try:
            persona = Persona.objects.get(user=request.user)
            persona.contrasena = new_password
            persona.save()
        except Persona.DoesNotExist:
            pass
        
        messages.success(request, 'Contraseña cambiada exitosamente.')
        return redirect('area_de_persona', id=user_rut)
    
    return render(request, 'core/changepassword_login.html', {'user_rut': user_rut})


# ============================================
# POSTS Y COMENTARIOS
# ============================================

def frontpage(request: HttpRequest) -> HttpResponse:
    """
    Vista principal del blog con lista de posts.
    
    Args:
        request: HttpRequest object (puede incluir parámetro 'search')
        
    Returns:
        HttpResponse: Renderiza la lista de posts con paginación
    """
    posts = Post.objects.select_related('author', 'hilo').annotate(
        comment_count=Count('comments')
    ).order_by('-date_added')
    
    # Búsqueda
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(intro__icontains=search_query) |
            Q(body__icontains=search_query)
        )
    
    # Paginación
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/frontpage.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })


def post_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Vista de detalle de un post.
    
    Args:
        request: HttpRequest object (puede incluir datos de comentario)
        slug: Slug único del post
        
    Returns:
        HttpResponse: Renderiza el detalle del post con comentarios
    """
    post = get_object_or_404(
        Post.objects.select_related('author', 'hilo').prefetch_related('comments__author'),
        slug=slug
    )
    
    # Manejar comentarios
    if request.method == 'POST':
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            
            # Asociar autor si está autenticado
            if request.user.is_authenticated:
                try:
                    persona = Persona.objects.select_related('tipousuario', 'user').get(user=request.user)
                    comment.author = persona
                    comment.name = f"{persona.nombre} {persona.apellido}"
                except Persona.DoesNotExist:
                    pass
            
            # Validar contenido inapropiado usando el sistema de moderación
            from core.moderation import validar_comentario
            es_valido, mensaje_error = validar_comentario(comment)
            
            if not es_valido:
                messages.error(request, mensaje_error)
                logger.warning(
                    f"Intento de crear comentario con contenido inapropiado. "
                    f"Usuario: {request.user.username if request.user.is_authenticated else 'anónimo'}. "
                    f"IP: {get_client_ip(request)}"
                )
                return redirect('post_detail', slug=slug)
            
            comment.save()
            
            # Procesar comentario para análisis de sentimientos
            try:
                procesar_comentario(comment)
            except Exception as e:
                logger.error(f"Error al procesar comentario: {e}", exc_info=True)
            
            messages.success(request, 'Comentario agregado exitosamente.')
            return redirect('post_detail', slug=slug)
        else:
            messages.error(request, 'Por favor, corrige los errores en el comentario.')
    else:
        form = CommentForm()
    
    # Obtener comentarios ordenados
    comments = post.comments.select_related('author').order_by('date_added')
    
    return render(request, 'core/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


@login_required
def form_post(request: HttpRequest) -> HttpResponse:
    """
    Vista para crear un nuevo post.
    
    Args:
        request: HttpRequest object con datos del formulario
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de crear
    """
    try:
        persona = Persona.objects.select_related('tipousuario', 'user').get(user=request.user)
    except Persona.DoesNotExist:
        messages.error(request, 'Debes tener un perfil para crear posts.')
        return redirect('form_persona')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        form.request = request
        
        if form.is_valid():
            post = form.save(commit=False)
            post.author = persona
            
            # Validar contenido inapropiado usando el sistema de moderación
            from core.moderation import validar_post
            es_valido, mensaje_error = validar_post(post)
            
            if not es_valido:
                messages.error(request, mensaje_error)
                logger.warning(
                    f"Intento de crear post con contenido inapropiado por usuario {persona.rut}. "
                    f"IP: {get_client_ip(request)}"
                )
                # Asegurar que el queryset de hilos esté disponible
                if hasattr(form, 'fields') and 'hilo' in form.fields:
                    form.fields['hilo'].queryset = Hilo.objects.all()
                return render(request, 'core/form_post.html', {'post_form': form, 'form': form, 'hilos': Hilo.objects.all()})
            
            post.save()
            
            messages.success(request, 'Post creado exitosamente.')
            return redirect('post_detail', slug=post.slug)
        else:
            messages.error(request, 'Por favor, corrige los errores.')
            # Asegurar que el queryset de hilos esté disponible en caso de error
            if hasattr(form, 'fields') and 'hilo' in form.fields:
                form.fields['hilo'].queryset = Hilo.objects.all()
            # Obtener todos los hilos para el template
            hilos = Hilo.objects.all().order_by('nombreHilo')
            return render(request, 'core/form_post.html', {'post_form': form, 'form': form, 'hilos': hilos})
    else:
        form = PostForm()
    
    # Asegurar que el queryset de hilos esté disponible
    if hasattr(form, 'fields') and 'hilo' in form.fields:
        form.fields['hilo'].queryset = Hilo.objects.all()
    
    # Obtener todos los hilos para el template
    hilos = Hilo.objects.all().order_by('nombreHilo')
    
    return render(request, 'core/form_post.html', {'post_form': form, 'form': form, 'hilos': hilos})


@login_required
def form_mod_post(request: HttpRequest, post_id: int) -> HttpResponse:
    """
    Vista para modificar un post.
    
    Args:
        request: HttpRequest object con datos del formulario
        post_id: ID del post a modificar
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de actualizar
    """
    post = get_object_or_404(
        Post.objects.select_related('author', 'hilo'),
        idPost=post_id
    )
    
    # Verificar que el usuario sea el autor
    try:
        persona = Persona.objects.select_related('tipousuario', 'user').get(user=request.user)
        if post.author != persona and not request.user.is_superuser:
            messages.error(request, 'No tienes permiso para editar este post.')
            return redirect('post_detail', slug=post.slug)
    except Persona.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado.')
        return redirect('form_persona')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        form.request = request
        
        if form.is_valid():
            post_actualizado = form.save(commit=False)
            
            # Validar contenido inapropiado usando el sistema de moderación
            from core.moderation import validar_post
            es_valido, mensaje_error = validar_post(post_actualizado)
            
            if not es_valido:
                messages.error(request, mensaje_error)
                logger.warning(
                    f"Intento de editar post con contenido inapropiado por usuario {persona.rut}. "
                    f"IP: {get_client_ip(request)}"
                )
                return render(request, 'core/form_mod_post.html', {'form': form, 'post': post})
            
            post_actualizado.save()
            messages.success(request, 'Post actualizado exitosamente.')
            return redirect('post_detail', slug=post.slug)
        else:
            messages.error(request, 'Por favor, corrige los errores.')
    else:
        form = PostForm(instance=post)
    
    return render(request, 'core/form_mod_post.html', {'form': form, 'post': post})


@login_required
def form_borrar_post(request: HttpRequest, id: int) -> HttpResponse:
    """
    Vista para eliminar un post.
    
    Args:
        request: HttpRequest object
        id: ID del post a eliminar
        
    Returns:
        HttpResponse: Renderiza confirmación o redirige después de eliminar
    """
    post = get_object_or_404(
        Post.objects.select_related('author', 'hilo'),
        idPost=id
    )
    
    # Verificar que el usuario sea el autor
    try:
        persona = Persona.objects.select_related('tipousuario', 'user').get(user=request.user)
        if post.author != persona and not request.user.is_superuser:
            messages.error(request, 'No tienes permiso para eliminar este post.')
            return redirect('post_detail', slug=post.slug)
    except Persona.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado.')
        return redirect('form_persona')
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post eliminado exitosamente.')
        return redirect('frontpage')
    
    return render(request, 'core/form_borrar_post.html', {'post': post})


@login_required
def editar_comentario(request: HttpRequest, comment_id: int) -> HttpResponse:
    """
    Vista para editar un comentario.
    
    Args:
        request: HttpRequest object con datos del formulario
        comment_id: ID del comentario a editar
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de actualizar
    """
    comment = get_object_or_404(
        Comment.objects.select_related('author', 'post', 'post__author'),
        id=comment_id
    )
    
    # Verificar que el usuario sea el autor
    try:
        persona = Persona.objects.select_related('tipousuario', 'user').get(user=request.user)
        if comment.author != persona and not request.user.is_superuser:
            messages.error(request, 'No tienes permiso para editar este comentario.')
            return redirect('post_detail', slug=comment.post.slug)
    except Persona.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado.')
        return redirect('form_persona')
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        form.request = request
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Comentario actualizado exitosamente.')
            return redirect('post_detail', slug=comment.post.slug)
        else:
            messages.error(request, 'Por favor, corrige los errores.')
    else:
        form = CommentForm(instance=comment)
    
    return render(request, 'core/editar_comentario.html', {
        'form': form,
        'comment': comment
    })


@login_required
def delete_comment(request: HttpRequest, comment_id: int) -> HttpResponse:
    """
    Vista para eliminar un comentario.
    
    Args:
        request: HttpRequest object
        comment_id: ID del comentario a eliminar
        
    Returns:
        HttpResponse: Renderiza confirmación o redirige después de eliminar
    """
    comment = get_object_or_404(
        Comment.objects.select_related('author', 'post', 'post__author'),
        id=comment_id
    )
    
    # Verificar que el usuario sea el autor
    try:
        persona = Persona.objects.select_related('tipousuario', 'user').get(user=request.user)
        if comment.author != persona and not request.user.is_superuser:
            messages.error(request, 'No tienes permiso para eliminar este comentario.')
            return redirect('post_detail', slug=comment.post.slug)
    except Persona.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado.')
        return redirect('form_persona')
    
    # Obtener el slug del post antes de borrar
    post_slug = comment.post.slug
    
    # Borrar el comentario (tanto GET como POST, ya que el template tiene confirmación JavaScript)
    comment.delete()
    messages.success(request, 'Comentario eliminado exitosamente.')
    return redirect('post_detail', slug=post_slug)


# ============================================
# NOTIFICACIONES
# ============================================

@login_required
def mostrar_notificaciones(request: HttpRequest) -> HttpResponse:
    """
    Vista para mostrar notificaciones del usuario.
    
    Args:
        request: HttpRequest object (puede incluir POST para marcar como leída)
        
    Returns:
        HttpResponse: Renderiza la lista de notificaciones
    """
    try:
        persona = Persona.objects.select_related('tipousuario', 'user').get(user=request.user)
        notificaciones = Notificacion.objects.filter(persona=persona).select_related('persona').order_by('-id')
        
        # Marcar como leídas
        if request.method == 'POST':
            notificacion_id = request.POST.get('notificacion_id')
            if notificacion_id:
                try:
                    notificacion = Notificacion.objects.get(id=notificacion_id, persona=persona)
                    notificacion.leida = True
                    notificacion.save()
                    messages.success(request, 'Notificación marcada como leída.')
                except Notificacion.DoesNotExist:
                    messages.error(request, 'Notificación no encontrada.')
        
        return render(request, 'core/mostrar_notificaciones.html', {
            'notificaciones': notificaciones
        })
    except Persona.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado.')
        return redirect('form_persona')


@login_required
def marcar_notificacion_leida(request: HttpRequest, notificacion_id: int) -> HttpResponse:
    """
    Vista para marcar una notificación como leída.
    
    Args:
        request: HttpRequest object
        notificacion_id: ID de la notificación
        
    Returns:
        HttpResponse: Redirige a la lista de notificaciones
    """
    try:
        persona = Persona.objects.select_related('tipousuario', 'user').get(user=request.user)
        notificacion = get_object_or_404(
            Notificacion.objects.select_related('persona'),
            id=notificacion_id,
            persona=persona
        )
        notificacion.leida = True
        notificacion.save()
        messages.success(request, 'Notificación marcada como leída.')
    except Persona.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado.')
    except Exception as e:
        logger.error(f"Error al marcar notificación como leída: {e}", exc_info=True)
        messages.error(request, 'Error al marcar la notificación.')
    
    return redirect('mostrar_notificaciones')


@login_required
def eliminar_notificacion(request: HttpRequest, notificacion_id: int) -> HttpResponse:
    """
    Vista para eliminar una notificación.
    
    Args:
        request: HttpRequest object
        notificacion_id: ID de la notificación
        
    Returns:
        HttpResponse: Redirige a la lista de notificaciones
    """
    try:
        persona = Persona.objects.select_related('tipousuario', 'user').get(user=request.user)
        notificacion = get_object_or_404(
            Notificacion.objects.select_related('persona'),
            id=notificacion_id,
            persona=persona
        )
        notificacion.delete()
        messages.success(request, 'Notificación eliminada.')
    except Persona.DoesNotExist:
        messages.error(request, 'No tienes un perfil asociado.')
    except Exception as e:
        logger.error(f"Error al eliminar notificación: {e}", exc_info=True)
        messages.error(request, 'Error al eliminar la notificación.')
    
    return redirect('mostrar_notificaciones')


@login_required
def marcar_notificacion_superusuario(request: HttpRequest, notificacion_id: int) -> HttpResponse:
    """
    Vista para marcar notificación de superusuario como leída.
    
    Args:
        request: HttpRequest object (debe ser superusuario)
        notificacion_id: ID de la notificación
        
    Returns:
        HttpResponse: Redirige al panel de administración
    """
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('index')
    
    try:
        notificacion = get_object_or_404(NotificacionSuperusuario, id=notificacion_id)
        notificacion.leida = True
        notificacion.save()
        messages.success(request, 'Notificación marcada como leída.')
    except Exception as e:
        logger.error(f"Error al marcar notificación superusuario: {e}", exc_info=True)
        messages.error(request, 'Error al marcar la notificación.')
    
    return redirect('adm')


# ============================================
# ANÁLISIS DE SENTIMIENTOS
# ============================================

def detectar_sentimiento(request: HttpRequest) -> JsonResponse:
    """
    Vista API para detectar sentimiento de un texto.
    
    Args:
        request: HttpRequest object con POST data ('texto')
        
    Returns:
        JsonResponse: JSON con el sentimiento detectado o error
    """
    if request.method == 'POST':
        texto = request.POST.get('texto', '')
        
        if not texto:
            return JsonResponse({'error': 'Texto no proporcionado'}, status=400)
        
        try:
            from .AI import predecir_sentimiento
            # Crear un objeto temporal para el análisis
            class ComentarioTemp:
                def __init__(self, body):
                    self.body = body
            
            comentario_temp = ComentarioTemp(texto)
            sentimiento = predecir_sentimiento(comentario_temp)
            
            return JsonResponse({
                'sentimiento': sentimiento,
                'texto': texto[:100]  # Primeros 100 caracteres
            })
        except Exception as e:
            logger.error(f"Error al detectar sentimiento: {e}", exc_info=True)
            return JsonResponse({'error': 'Error al procesar el texto'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============================================
# MANEJO DE ERRORES CSRF
# ============================================

@requires_csrf_token
def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponseForbidden:
    """
    Vista personalizada para errores CSRF.
    
    Args:
        request: HttpRequest object
        reason: Razón del error CSRF
        
    Returns:
        HttpResponseForbidden: Página de error personalizada
    """
    logger.warning(f"Error CSRF detectado - IP: {get_client_ip(request)}, Reason: {reason}")


# ============================================
# SISTEMA DE MODERACIÓN Y REPORTES
# ============================================

@login_required
def reportar_post(request: HttpRequest, post_id: int) -> HttpResponse:
    """
    Permite a los usuarios reportar un post por contenido inapropiado.
    
    Args:
        request: HttpRequest object
        post_id: ID del post a reportar
        
    Returns:
        HttpResponse: JSON response o redirect
    """
    try:
        post = get_object_or_404(Post, idPost=post_id)
        
        if request.method == 'POST':
            razon = request.POST.get('razon', 'Contenido inapropiado')
            
            from core.moderation import reportar_contenido
            exito = reportar_contenido(
                post_id=post_id,
                razon=razon,
                usuario_reportante=request.user
            )
            
            if exito:
                messages.success(
                    request, 
                    'Post reportado exitosamente. Nuestro equipo de moderación lo revisará.'
                )
                logger.info(
                    f"Post {post_id} reportado por usuario {request.user.username}. "
                    f"Razón: {razon}. IP: {get_client_ip(request)}"
                )
            else:
                messages.error(request, 'Error al reportar el post. Por favor, intenta nuevamente.')
            
            return redirect('post_detail', slug=post.slug)
        
        # Si es GET, mostrar formulario de reporte
        return render(request, 'core/reportar_post.html', {
            'post': post
        })
    
    except Exception as e:
        logger.error(f"Error al reportar post: {e}", exc_info=True)
        messages.error(request, 'Error al procesar el reporte.')
        return redirect('frontpage')


@login_required
def reportar_comentario(request: HttpRequest, comment_id: int) -> HttpResponse:
    """
    Permite a los usuarios reportar un comentario por contenido inapropiado.
    
    Args:
        request: HttpRequest object
        comment_id: ID del comentario a reportar
        
    Returns:
        HttpResponse: JSON response o redirect
    """
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        
        if request.method == 'POST':
            razon = request.POST.get('razon', 'Contenido inapropiado')
            
            from core.moderation import reportar_contenido
            exito = reportar_contenido(
                comment_id=comment_id,
                razon=razon,
                usuario_reportante=request.user
            )
            
            if exito:
                messages.success(
                    request, 
                    'Comentario reportado exitosamente. Nuestro equipo de moderación lo revisará.'
                )
                logger.info(
                    f"Comentario {comment_id} reportado por usuario {request.user.username}. "
                    f"Razón: {razon}. IP: {get_client_ip(request)}"
                )
            else:
                messages.error(request, 'Error al reportar el comentario. Por favor, intenta nuevamente.')
            
            return redirect('post_detail', slug=comment.post.slug)
        
        # Si es GET, mostrar formulario de reporte
        return render(request, 'core/reportar_comentario.html', {
            'comment': comment
        })
    
    except Exception as e:
        logger.error(f"Error al reportar comentario: {e}", exc_info=True)
        messages.error(request, 'Error al procesar el reporte.')
        return redirect('frontpage')


@login_required
def panel_moderacion(request: HttpRequest) -> HttpResponse:
    """
    Panel de moderación para administradores.
    Muestra posts y comentarios reportados.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse: Panel de moderación
    """
    # Solo superusuarios pueden acceder
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('frontpage')
    
    from core.moderation import obtener_posts_reportados
    
    posts_reportados = obtener_posts_reportados()
    
    return render(request, 'core/panel_moderacion.html', {
        'posts_reportados': posts_reportados
    })


@login_required
def moderar_post(request: HttpRequest, post_id: int, accion: str) -> HttpResponse:
    """
    Permite a los moderadores aprobar o rechazar posts reportados.
    
    Args:
        request: HttpRequest object
        post_id: ID del post a moderar
        accion: 'aprobar' o 'rechazar'
        
    Returns:
        HttpResponse: Redirect al panel de moderación
    """
    # Solo superusuarios pueden moderar
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('frontpage')
    
    try:
        from core.moderation import moderar_post as moderar
        aprobar = (accion == 'aprobar')
        
        exito = moderar(post_id, aprobar, request.user)
        
        if exito:
            if aprobar:
                messages.success(request, 'Post aprobado exitosamente.')
            else:
                messages.success(request, 'Post rechazado y eliminado exitosamente.')
        else:
            messages.error(request, 'Error al moderar el post.')
    
    except Exception as e:
        logger.error(f"Error al moderar post: {e}", exc_info=True)
        messages.error(request, 'Error al procesar la moderación.')
    
    return redirect('panel_moderacion')
