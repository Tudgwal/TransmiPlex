from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """
    Divise une chaîne selon le séparateur donné
    """
    return value.split(arg)