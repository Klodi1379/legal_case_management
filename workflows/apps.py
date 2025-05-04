"""
Django app configuration for workflows.
"""

from django.apps import AppConfig


class WorkflowsConfig(AppConfig):
    """Configuration for the workflows app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workflows'
    verbose_name = 'Workflow Automation'
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        This method is called when Django starts and can be used to
        register signal handlers or perform other initialization tasks.
        """
        # Import signal handlers
        import workflows.signals
