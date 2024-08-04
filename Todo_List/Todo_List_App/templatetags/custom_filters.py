from django import template

register = template.Library()

@register.filter
def toggle_order(current_order):
    return 'asc' if current_order == 'desc' else 'desc'
