from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except (ValueError, TypeError):
        return ''

@register.filter
def divi(value, arg):
    try:
        return round(value / arg,2)
    except (ValueError, TypeError):
        return ''