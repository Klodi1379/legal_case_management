"""
Custom template tags and filters for the core app.
"""

import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def pprint(value):
    """
    Pretty print JSON data.
    
    Args:
        value: JSON data to format
        
    Returns:
        Formatted JSON string
    """
    if value is None:
        return ""
        
    try:
        if isinstance(value, str):
            value = json.loads(value)
        return mark_safe(json.dumps(value, indent=2))
    except:
        return value
