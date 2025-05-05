"""
Template tags for AI services.

This module provides custom template tags and filters for AI services.
"""

from django import template
from django.template.defaultfilters import floatformat
from ai_services.models import LLMModel
from ai_services import settings as ai_settings

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

@register.filter
def replace(value, arg):
    """
    Replace all occurrences of the first argument with the second argument.

    Args:
        value: The string to search in
        arg: A string in the format "old,new"

    Returns:
        The string with all occurrences of old replaced by new
    """
    try:
        old, new = arg.split(',')
        return value.replace(old, new)
    except (ValueError, AttributeError):
        return value

@register.simple_tag
def get_active_model():
    """
    Get the active LLM model.

    Returns:
        The active LLM model, or None if no active model exists
    """
    try:
        return LLMModel.objects.filter(is_active=True).first()
    except Exception:
        return None

@register.simple_tag
def is_using_mock_service():
    """
    Check if the system is using mock services.

    Returns:
        True if using mock services, False otherwise
    """
    # Check if AI features are enabled
    if not ai_settings.ENABLE_AI_FEATURES:
        return True

    # Check if there's an active model
    model = LLMModel.objects.filter(is_active=True).first()
    if not model:
        return True

    return False
