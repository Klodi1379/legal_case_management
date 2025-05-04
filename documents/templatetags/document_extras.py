from django import template
import os

register = template.Library()

@register.filter
def get_file_icon(filename):
    """
    Return the appropriate Font Awesome icon class based on file extension.
    """
    if not filename:
        return "fa-file"
    
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in ['.doc', '.docx']:
        return "fa-file-word"
    elif ext == '.pdf':
        return "fa-file-pdf"
    elif ext == '.txt':
        return "fa-file-alt"
    else:
        return "fa-file"

@register.filter
def split(value, key):
    """
    Split a string by the given key and return the specified index.
    """
    if not value:
        return ""
    
    parts = value.split(key)
    if len(parts) > 0:
        return parts[-1]  # Return the last part
    return value
