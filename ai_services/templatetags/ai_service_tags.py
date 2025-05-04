"""
Template tags for AI services.

This module provides custom template tags and filters for AI services.
"""

from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def divisor(value, arg):
    """
    Divide the value by the argument.
    
    Args:
        value: The numerator
        arg: The denominator
        
    Returns:
        The result of the division, or 0 if the denominator is 0
    """
    try:
        if arg == 0:
            return 0
        return float(value) / float(arg) * 100
    except (ValueError, TypeError):
        return 0
        
@register.filter
def get(dictionary, key):
    """
    Get a value from a dictionary by key.
    
    Args:
        dictionary: The dictionary
        key: The key
        
    Returns:
        The value for the key, or None if the key is not found
    """
    return dictionary.get(key)
