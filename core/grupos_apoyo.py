"""
Sistema de Grupos de Apoyo para ZenMindConnect.
Permite crear grupos temáticos y sesiones grupales de videollamada.
"""
import logging
from typing import List, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from .models import (
    GrupoApoyo, MiembroGrupo, SesionGrupo, RecursoGrupo,
    Persona, Psicologo, VideoCallRoom
)

logger = logging.getLogger(__name__)


def crear_grupo_apoyo(
    nombre: str,
    descripcion: str,
    tema: str,
    creado_por: Persona,
    psicologo_moderador: Optional[Psicologo] = None,
    max_miembros: int = 20,
    is_publico: bool = True
) -> GrupoApoyo:
    """
    Crea un nuevo grupo de apoyo.
    
    Args:
        nombre: Nombre del grupo
        descripcion: Descripción del grupo
        tema: Tema del grupo
        creado_por: Persona que crea el grupo
        psicologo_moderador: Psicólogo moderador (opcional)
        max_miembros: Máximo de miembros
        is_publico: Si el grupo es público
        
    Returns:
        GrupoApoyo creado
    """
    try:
        grupo = GrupoApoyo.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            tema=tema,
            creado_por=creado_por,
            psicologo_moderador=psicologo_moderador,
            max_miembros=max_miembros,
            is_publico=is_publico
        )
        
        # Agregar creador como miembro y moderador
        MiembroGrupo.objects.create(
            grupo=grupo,
            persona=creado_por,
            es_moderador=True
        )
        
        logger.info(f"Grupo de apoyo '{nombre}' creado por {creado_por}")
        
        return grupo
        
    except Exception as e:
        logger.error(f"Error al crear grupo de apoyo: {e}")
        raise


def unirse_grupo(grupo: GrupoApoyo, persona: Persona) -> Tuple[bool, str]:
    """
    Agrega una persona a un grupo de apoyo.
    
    Args:
        grupo: Grupo de apoyo
        persona: Persona que se une
        
    Returns:
        Tuple: (exitoso, mensaje)
    """
    try:
        # Verificar que el grupo esté activo
        if not grupo.is_activo:
            return False, "Este grupo no está activo."
        
        # Verificar que haya espacio
        if not grupo.tiene_espacio():
            return False, "Este grupo ha alcanzado su capacidad máxima."
        
        # Verificar que no sea miembro ya
        if MiembroGrupo.objects.filter(grupo=grupo, persona=persona, is_activo=True).exists():
            return False, "Ya eres miembro de este grupo."
        
        # Agregar como miembro
        MiembroGrupo.objects.create(
            grupo=grupo,
            persona=persona,
            is_activo=True
        )
        
        logger.info(f"{persona} se unió al grupo {grupo.nombre}")
        
        return True, "Te has unido al grupo exitosamente."
        
    except Exception as e:
        logger.error(f"Error al unirse al grupo: {e}")
        return False, "Ocurrió un error al unirse al grupo."


def salir_grupo(grupo: GrupoApoyo, persona: Persona) -> Tuple[bool, str]:
    """
    Remueve una persona de un grupo de apoyo.
    
    Args:
        grupo: Grupo de apoyo
        persona: Persona que sale
        
    Returns:
        Tuple: (exitoso, mensaje)
    """
    try:
        miembro = MiembroGrupo.objects.filter(
            grupo=grupo,
            persona=persona,
            is_activo=True
        ).first()
        
        if not miembro:
            return False, "No eres miembro de este grupo."
        
        # No permitir que el creador salga si es el único moderador
        if miembro.es_moderador and grupo.creado_por == persona:
            otros_moderadores = MiembroGrupo.objects.filter(
                grupo=grupo,
                es_moderador=True,
                is_activo=True
            ).exclude(persona=persona).exists()
            
            if not otros_moderadores:
                return False, "No puedes salir del grupo. Eres el único moderador."
        
        miembro.is_activo = False
        miembro.save()
        
        logger.info(f"{persona} salió del grupo {grupo.nombre}")
        
        return True, "Has salido del grupo exitosamente."
        
    except Exception as e:
        logger.error(f"Error al salir del grupo: {e}")
        return False, "Ocurrió un error al salir del grupo."


def crear_sesion_grupo(
    grupo: GrupoApoyo,
    fecha_programada: timezone.datetime,
    psicologo_facilitador: Optional[Psicologo] = None,
    tema_sesion: str = ""
) -> SesionGrupo:
    """
    Crea una sesión grupal de videollamada.
    
    Args:
        grupo: Grupo de apoyo
        fecha_programada: Fecha y hora programada
        psicologo_facilitador: Psicólogo facilitador (opcional)
        tema_sesion: Tema de la sesión
        
    Returns:
        SesionGrupo creada
    """
    try:
        # Crear sala de videollamada para el grupo si no existe
        if not grupo.sala_videocall:
            # Crear nombre único para la sala
            nombre_sala = f"grupo_{grupo.id}_{grupo.nombre.lower().replace(' ', '_')}"
            
            # Crear sala usando la función existente
            sala = VideoCallRoom.objects.create(
                name=nombre_sala,
                created_by=grupo.creado_por,
                room_type='group',
                max_participants=grupo.max_miembros,
                is_active=True
            )
            
            grupo.sala_videocall = sala
            grupo.save()
        
        # Crear sesión
        sesion = SesionGrupo.objects.create(
            grupo=grupo,
            sala_videocall=grupo.sala_videocall,
            fecha_programada=fecha_programada,
            psicologo_facilitador=psicologo_facilitador,
            tema_sesion=tema_sesion,
            is_activa=False
        )
        
        logger.info(f"Sesión grupal creada para {grupo.nombre} el {fecha_programada}")
        
        return sesion
        
    except Exception as e:
        logger.error(f"Error al crear sesión grupal: {e}")
        raise


def obtener_grupos_disponibles(persona: Optional[Persona] = None, tema: Optional[str] = None) -> List[GrupoApoyo]:
    """
    Obtiene grupos de apoyo disponibles.
    
    Args:
        persona: Persona (para filtrar grupos donde ya es miembro)
        tema: Tema específico (opcional)
        
    Returns:
        Lista de grupos disponibles
    """
    grupos = GrupoApoyo.objects.filter(is_activo=True)
    
    # Filtrar por tema si se especifica
    if tema:
        grupos = grupos.filter(tema=tema)
    
    # Si se especifica persona, excluir grupos donde ya es miembro
    if persona:
        grupos_miembro = MiembroGrupo.objects.filter(
            persona=persona,
            is_activo=True
        ).values_list('grupo_id', flat=True)
        
        grupos = grupos.exclude(id__in=grupos_miembro)
    
    return grupos.order_by('-created_at')


def obtener_grupos_miembro(persona: Persona) -> List[GrupoApoyo]:
    """
    Obtiene los grupos donde la persona es miembro.
    
    Args:
        persona: Persona
        
    Returns:
        Lista de grupos
    """
    grupos_ids = MiembroGrupo.objects.filter(
        persona=persona,
        is_activo=True
    ).values_list('grupo_id', flat=True)
    
    return GrupoApoyo.objects.filter(
        id__in=grupos_ids,
        is_activo=True
    ).order_by('-created_at')


def compartir_recurso(
    grupo: GrupoApoyo,
    titulo: str,
    descripcion: str,
    tipo: str,
    compartido_por: Persona,
    url: Optional[str] = None,
    archivo = None
) -> RecursoGrupo:
    """
    Comparte un recurso en un grupo de apoyo.
    
    Args:
        grupo: Grupo de apoyo
        titulo: Título del recurso
        descripcion: Descripción
        tipo: Tipo de recurso
        compartido_por: Persona que comparte
        url: URL del recurso (opcional)
        archivo: Archivo (opcional)
        
    Returns:
        RecursoGrupo creado
    """
    try:
        # Verificar que la persona sea miembro del grupo
        if not MiembroGrupo.objects.filter(grupo=grupo, persona=compartido_por, is_activo=True).exists():
            raise ValueError("Debes ser miembro del grupo para compartir recursos.")
        
        recurso = RecursoGrupo.objects.create(
            grupo=grupo,
            titulo=titulo,
            descripcion=descripcion,
            tipo=tipo,
            compartido_por=compartido_por,
            url=url,
            archivo=archivo
        )
        
        logger.info(f"Recurso '{titulo}' compartido en grupo {grupo.nombre} por {compartido_por}")
        
        return recurso
        
    except Exception as e:
        logger.error(f"Error al compartir recurso: {e}")
        raise

