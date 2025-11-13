"""
Vistas para el sistema de Grupos de Apoyo.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from typing import Tuple
from .models import (
    Persona, GrupoApoyo, MiembroGrupo, SesionGrupo, RecursoGrupo,
    Psicologo, VideoCallRoom
)
from .grupos_apoyo import (
    crear_grupo_apoyo, unirse_grupo, salir_grupo,
    crear_sesion_grupo, obtener_grupos_disponibles,
    obtener_grupos_miembro, compartir_recurso
)
from .decorators import get_client_ip

logger = logging.getLogger(__name__)


@login_required
def listar_grupos(request: HttpRequest) -> HttpResponse:
    """
    Lista todos los grupos de apoyo disponibles.
    
    Args:
        request: HttpRequest
        
    Returns:
        HttpResponse: Renderiza la lista de grupos
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        
        # Obtener tema de filtro
        tema_filtro = request.GET.get('tema', '')
        
        # Obtener grupos disponibles (donde no es miembro)
        grupos_disponibles = obtener_grupos_disponibles(persona, tema_filtro if tema_filtro else None)
        
        # Obtener grupos donde es miembro
        grupos_miembro = obtener_grupos_miembro(persona)
        
        # Paginación
        paginator = Paginator(grupos_disponibles, 12)
        page = request.GET.get('page')
        grupos_paginados = paginator.get_page(page)
        
        context = {
            'persona': persona,
            'grupos_disponibles': grupos_paginados,
            'grupos_miembro': grupos_miembro,
            'tema_filtro': tema_filtro,
            'temas_disponibles': GrupoApoyo.TEMA_CHOICES,
        }
        
        return render(request, 'core/listar_grupos.html', context)
        
    except Persona.DoesNotExist:
        messages.error(request, 'Debes tener un perfil para ver grupos de apoyo.')
        return redirect('form_persona')
    except Exception as e:
        logger.error(f"Error en listar_grupos: {e}", exc_info=True)
        messages.error(request, 'Ocurrió un error al cargar los grupos.')
        return redirect('index')


@login_required
def detalle_grupo(request: HttpRequest, grupo_id: int) -> HttpResponse:
    """
    Muestra el detalle de un grupo de apoyo.
    
    Args:
        request: HttpRequest
        grupo_id: ID del grupo
        
    Returns:
        HttpResponse: Renderiza el detalle del grupo
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        grupo = get_object_or_404(GrupoApoyo, id=grupo_id, is_activo=True)
        
        # Verificar si es miembro
        es_miembro = MiembroGrupo.objects.filter(
            grupo=grupo,
            persona=persona,
            is_activo=True
        ).exists()
        
        # Obtener miembros activos
        miembros = MiembroGrupo.objects.filter(
            grupo=grupo,
            is_activo=True
        ).select_related('persona').order_by('-fecha_union')[:10]
        
        # Obtener sesiones próximas
        sesiones = SesionGrupo.objects.filter(
            grupo=grupo,
            fecha_programada__gte=timezone.now()
        ).order_by('fecha_programada')[:5]
        
        # Obtener recursos recientes
        recursos = RecursoGrupo.objects.filter(
            grupo=grupo
        ).order_by('-created_at')[:10]
        
        context = {
            'persona': persona,
            'grupo': grupo,
            'es_miembro': es_miembro,
            'miembros': miembros,
            'sesiones': sesiones,
            'recursos': recursos,
        }
        
        return render(request, 'core/detalle_grupo.html', context)
        
    except Exception as e:
        logger.error(f"Error en detalle_grupo: {e}", exc_info=True)
        messages.error(request, 'Ocurrió un error al cargar el grupo.')
        return redirect('listar_grupos')


@login_required
def crear_grupo(request: HttpRequest) -> HttpResponse:
    """
    Crea un nuevo grupo de apoyo.
    
    Args:
        request: HttpRequest
        
    Returns:
        HttpResponse: Renderiza formulario o redirige después de crear
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        
        if request.method == 'POST':
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            tema = request.POST.get('tema', '')
            max_miembros = int(request.POST.get('max_miembros', 20))
            is_publico = request.POST.get('is_publico') == 'on'
            psicologo_id = request.POST.get('psicologo_moderador', '')
            
            # Validaciones
            if not nombre or not descripcion or not tema:
                messages.error(request, 'Todos los campos son obligatorios.')
                return render(request, 'core/crear_grupo.html', {
                    'persona': persona,
                    'temas': GrupoApoyo.TEMA_CHOICES,
                    'psicologos': Psicologo.objects.all(),
                })
            
            psicologo_moderador = None
            if psicologo_id:
                try:
                    psicologo_moderador = Psicologo.objects.get(id=psicologo_id)
                except Psicologo.DoesNotExist:
                    pass
            
            # Crear grupo
            grupo = crear_grupo_apoyo(
                nombre=nombre,
                descripcion=descripcion,
                tema=tema,
                creado_por=persona,
                psicologo_moderador=psicologo_moderador,
                max_miembros=max_miembros,
                is_publico=is_publico
            )
            
            messages.success(request, f'Grupo "{grupo.nombre}" creado exitosamente.')
            return redirect('detalle_grupo', grupo_id=grupo.id)
        
        # GET: Mostrar formulario
        context = {
            'persona': persona,
            'temas': GrupoApoyo.TEMA_CHOICES,
            'psicologos': Psicologo.objects.all(),
        }
        
        return render(request, 'core/crear_grupo.html', context)
        
    except Persona.DoesNotExist:
        messages.error(request, 'Debes tener un perfil para crear grupos.')
        return redirect('form_persona')
    except Exception as e:
        logger.error(f"Error en crear_grupo: {e}", exc_info=True)
        messages.error(request, 'Ocurrió un error al crear el grupo.')
        return redirect('listar_grupos')


@login_required
@require_http_methods(["POST"])
def unirse_grupo_view(request: HttpRequest, grupo_id: int) -> HttpResponse:
    """
    Permite a un usuario unirse a un grupo de apoyo.
    
    Args:
        request: HttpRequest
        grupo_id: ID del grupo
        
    Returns:
        HttpResponse: Redirige al detalle del grupo
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        grupo = get_object_or_404(GrupoApoyo, id=grupo_id, is_activo=True)
        
        exito, mensaje = unirse_grupo(grupo, persona)
        
        if exito:
            messages.success(request, mensaje)
        else:
            messages.error(request, mensaje)
        
        return redirect('detalle_grupo', grupo_id=grupo.id)
        
    except Exception as e:
        logger.error(f"Error en unirse_grupo_view: {e}", exc_info=True)
        messages.error(request, 'Ocurrió un error al unirse al grupo.')
        return redirect('listar_grupos')


@login_required
@require_http_methods(["POST"])
def salir_grupo_view(request: HttpRequest, grupo_id: int) -> HttpResponse:
    """
    Permite a un usuario salir de un grupo de apoyo.
    
    Args:
        request: HttpRequest
        grupo_id: ID del grupo
        
    Returns:
        HttpResponse: Redirige a la lista de grupos
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        grupo = get_object_or_404(GrupoApoyo, id=grupo_id)
        
        exito, mensaje = salir_grupo(grupo, persona)
        
        if exito:
            messages.success(request, mensaje)
        else:
            messages.error(request, mensaje)
        
        return redirect('listar_grupos')
        
    except Exception as e:
        logger.error(f"Error en salir_grupo_view: {e}", exc_info=True)
        messages.error(request, 'Ocurrió un error al salir del grupo.')
        return redirect('listar_grupos')


@login_required
def sala_grupo(request: HttpRequest, grupo_id: int) -> HttpResponse:
    """
    Sala de videollamada grupal para un grupo de apoyo.
    
    Args:
        request: HttpRequest
        grupo_id: ID del grupo
        
    Returns:
        HttpResponse: Renderiza la sala de videollamada
    """
    try:
        persona = get_object_or_404(Persona, user=request.user)
        grupo = get_object_or_404(GrupoApoyo, id=grupo_id, is_activo=True)
        
        # Verificar que sea miembro
        es_miembro = MiembroGrupo.objects.filter(
            grupo=grupo,
            persona=persona,
            is_activo=True
        ).exists()
        
        if not es_miembro:
            messages.error(request, 'Debes ser miembro del grupo para acceder a la sala.')
            return redirect('detalle_grupo', grupo_id=grupo.id)
        
        # Crear sala si no existe
        if not grupo.sala_videocall:
            nombre_sala = f"grupo_{grupo.id}_{grupo.nombre.lower().replace(' ', '_')}"
            sala = VideoCallRoom.objects.create(
                name=nombre_sala,
                created_by=grupo.creado_por,
                room_type='group',
                max_participants=grupo.max_miembros,
                is_active=True
            )
            grupo.sala_videocall = sala
            grupo.save()
        
        # Redirigir a la sala de videollamada existente
        return redirect('videocall_room', room_name=grupo.sala_videocall.name)
        
    except Exception as e:
        logger.error(f"Error en sala_grupo: {e}", exc_info=True)
        messages.error(request, 'Ocurrió un error al acceder a la sala.')
        return redirect('detalle_grupo', grupo_id=grupo_id)

