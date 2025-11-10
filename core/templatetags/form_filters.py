"""
Filtros personalizados para formularios Django.
"""
from django import template

register = template.Library()


@register.filter(name='add_attrs')
def add_attrs(field, attrs_string):
    """
    Agrega atributos HTML a un campo de formulario.
    
    Args:
        field: Campo del formulario Django
        attrs_string: String con atributos en formato "key1:value1,key2:value2"
    
    Returns:
        Campo con atributos agregados
    """
    if not field or not attrs_string:
        return field
    
    # Parsear los atributos
    attrs_dict = {}
    for attr_pair in attrs_string.split(','):
        if ':' in attr_pair:
            key, value = attr_pair.split(':', 1)
            attrs_dict[key.strip()] = value.strip()
    
    # Agregar atributos al widget
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        widget = field.field.widget
        if hasattr(widget, 'attrs'):
            widget.attrs.update(attrs_dict)
    
    return field

