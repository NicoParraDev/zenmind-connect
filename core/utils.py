"""
Utilidades y funciones auxiliares para validaciones y operaciones comunes.
"""
import re
import logging

logger = logging.getLogger(__name__)


def validar_rut_chileno(rut):
    """
    Valida un RUT chileno.
    
    Args:
        rut: String con el RUT (puede incluir puntos y guión)
    
    Returns:
        tuple: (es_valido: bool, rut_limpio: str, mensaje_error: str)
    """
    if not rut:
        return False, "", "El RUT no puede estar vacío"
    
    # Limpiar el RUT (quitar puntos y espacios)
    rut_limpio = rut.replace('.', '').replace(' ', '').replace('-', '').upper()
    
    if len(rut_limpio) < 8 or len(rut_limpio) > 9:
        return False, rut_limpio, "El RUT debe tener entre 8 y 9 dígitos"
    
    # Separar número y dígito verificador
    if len(rut_limpio) == 8:
        numero = rut_limpio[:-1]
        dv = rut_limpio[-1]
    else:
        numero = rut_limpio[:-1]
        dv = rut_limpio[-1]
    
    # Validar que el número sea solo dígitos
    if not numero.isdigit():
        return False, rut_limpio, "El número del RUT debe contener solo dígitos"
    
    # Calcular dígito verificador
    multiplicador = 2
    suma = 0
    
    for digito in reversed(numero):
        suma += int(digito) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2
    
    resto = suma % 11
    dv_calculado = 11 - resto
    
    if dv_calculado == 11:
        dv_calculado = '0'
    elif dv_calculado == 10:
        dv_calculado = 'K'
    else:
        dv_calculado = str(dv_calculado)
    
    if dv != dv_calculado:
        return False, rut_limpio, f"El dígito verificador es incorrecto. Debería ser {dv_calculado}"
    
    return True, rut_limpio, ""


def formatear_rut(rut):
    """
    Formatea un RUT chileno con puntos y guión.
    
    Args:
        rut: String con el RUT (limpio o con formato)
    
    Returns:
        str: RUT formateado (ej: 12.345.678-9)
    """
    rut_limpio = rut.replace('.', '').replace(' ', '').replace('-', '').upper()
    
    if len(rut_limpio) < 8:
        return rut
    
    numero = rut_limpio[:-1]
    dv = rut_limpio[-1]
    
    # Agregar puntos cada 3 dígitos desde la derecha
    numero_formateado = ''
    for i, digito in enumerate(reversed(numero)):
        if i > 0 and i % 3 == 0:
            numero_formateado = '.' + numero_formateado
        numero_formateado = digito + numero_formateado
    
    return f"{numero_formateado}-{dv}"


def validar_telefono_chileno(telefono):
    """
    Valida un número de teléfono chileno.
    
    Args:
        telefono: String con el número de teléfono
    
    Returns:
        tuple: (es_valido: bool, mensaje_error: str)
    """
    if not telefono:
        return False, "El teléfono no puede estar vacío"
    
    # Limpiar el teléfono (quitar espacios, guiones, paréntesis)
    telefono_limpio = re.sub(r'[\s\-\(\)]', '', telefono)
    
    # Validar formato chileno
    # Puede empezar con +56, 56, o directamente con 9
    patron = r'^(\+?56)?9\d{8}$'
    
    if not re.match(patron, telefono_limpio):
        return False, "El formato del teléfono no es válido. Debe ser: +56912345678 o 912345678"
    
    return True, ""


def limpiar_telefono(telefono):
    """
    Limpia y normaliza un número de teléfono chileno.
    
    Args:
        telefono: String con el número de teléfono
    
    Returns:
        str: Teléfono limpio (formato: +56912345678)
    """
    if not telefono:
        return ""
    
    telefono_limpio = re.sub(r'[\s\-\(\)]', '', telefono)
    
    # Si no empieza con +56, agregarlo
    if telefono_limpio.startswith('56'):
        telefono_limpio = '+' + telefono_limpio
    elif telefono_limpio.startswith('9'):
        telefono_limpio = '+56' + telefono_limpio
    elif not telefono_limpio.startswith('+56'):
        telefono_limpio = '+56' + telefono_limpio
    
    return telefono_limpio

