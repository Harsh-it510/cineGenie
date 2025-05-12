from django import template
from django.shortcuts import reverse
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def url_with_query(url_name, **kwargs):
    """Generate a URL with query parameters."""
    url = reverse(url_name)
    if kwargs:
        url += '?' + '&'.join([f"{k}={v}" for k, v in kwargs.items()])
    return url 