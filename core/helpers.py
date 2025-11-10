"""
Funciones helper para la aplicación ZenMindConnect.
Incluye utilidades para validación, email, y otras funciones comunes.
"""
from datetime import date, datetime
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


# ============================================
# FUNCIONES DE VALIDACIÓN DE FECHAS
# ============================================

def validar_fecha_futura(fecha, mensaje_error="La fecha no puede ser en el pasado"):
    """
    Valida que una fecha sea futura (no en el pasado).
    
    Args:
        fecha: Objeto date o datetime a validar
        mensaje_error: Mensaje personalizado de error
    
    Returns:
        bool: True si la fecha es válida
    
    Raises:
        ValidationError: Si la fecha es en el pasado
    """
    if fecha is None:
        return True
    
    # Convertir datetime a date si es necesario
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    
    hoy = date.today()
    
    if fecha < hoy:
        raise ValidationError(mensaje_error)
    
    return True


def validar_fecha_no_muy_lejana(fecha, dias_maximos=365, mensaje_error=None):
    """
    Valida que una fecha no sea muy lejana en el futuro.
    
    Args:
        fecha: Objeto date o datetime a validar
        dias_maximos: Número máximo de días en el futuro permitidos (default: 365)
        mensaje_error: Mensaje personalizado de error
    
    Returns:
        bool: True si la fecha es válida
    
    Raises:
        ValidationError: Si la fecha es muy lejana
    """
    if fecha is None:
        return True
    
    # Convertir datetime a date si es necesario
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    
    hoy = date.today()
    fecha_maxima = hoy.replace(year=hoy.year + 1)  # Aproximadamente 365 días
    
    if fecha > fecha_maxima:
        if mensaje_error is None:
            mensaje_error = f"La fecha no puede ser más de {dias_maximos} días en el futuro."
        raise ValidationError(mensaje_error)
    
    return True


def validar_fecha_agenda(fecha, psicologo=None, agenda_actual=None):
    """
    Valida una fecha para una agenda, verificando que:
    1. No sea en el pasado
    2. No exista otra agenda para el mismo psicólogo en esa fecha
    
    Args:
        fecha: Objeto date a validar
        psicologo: Instancia de Psicologo (opcional)
        agenda_actual: Instancia de Agenda actual (para edición, opcional)
    
    Returns:
        bool: True si la fecha es válida
    
    Raises:
        ValidationError: Si la fecha no es válida
    """
    from core.models import Agenda
    
    # Validar que no sea en el pasado
    validar_fecha_futura(fecha, "No es posible seleccionar una fecha que ya haya pasado.")
    
    # Validar que no exista otra agenda para el mismo psicólogo en la misma fecha
    if psicologo:
        agenda_existente = Agenda.objects.filter(
            psicologo=psicologo,
            data=fecha
        )
        
        # Excluir la instancia actual si estamos editando
        if agenda_actual and agenda_actual.pk:
            agenda_existente = agenda_existente.exclude(pk=agenda_actual.pk)
        
        if agenda_existente.exists():
            raise ValidationError(
                "Ya existe una agenda para este psicólogo en esta fecha. Por favor, seleccione otra fecha."
            )
    
    return True


def validar_cita_puede_modificarse(horario_agenda):
    """
    Valida que una cita pueda ser modificada o cancelada.
    
    Args:
        horario_agenda: Instancia de HorarioAgenda
    
    Returns:
        bool: True si la cita puede modificarse
    
    Raises:
        ValidationError: Si la cita no puede modificarse
    """
    if horario_agenda is None:
        raise ValidationError("La cita no existe.")
    
    # Verificar que la cita no sea del pasado
    if horario_agenda.agenda.data < date.today():
        raise ValidationError("No puedes modificar o cancelar una cita que ya pasó.")
    
    return True
