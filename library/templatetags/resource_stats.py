from django import template

register = template.Library()

@register.filter
def count_by_type(resources, resource_type):
    return resources.filter(resource_type=resource_type).count()

@register.filter
def count_authors(resources):
    return resources.values('author').distinct().count()