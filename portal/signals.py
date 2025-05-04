# portal/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import PortalAccess

User = get_user_model()

@receiver(post_save, sender=User)
def create_portal_access(sender, instance, created, **kwargs):
    """
    Create portal access for new client users.
    """
    if created and instance.is_client:
        PortalAccess.objects.create(user=instance)

@receiver(post_save, sender=User)
def update_portal_access(sender, instance, **kwargs):
    """
    Update portal access when user is changed.
    """
    if instance.is_client:
        # Create portal access if it doesn't exist
        PortalAccess.objects.get_or_create(user=instance)
    else:
        # Deactivate portal access if user is no longer a client
        try:
            portal_access = instance.portal_access
            if portal_access.is_active:
                portal_access.is_active = False
                portal_access.save()
        except PortalAccess.DoesNotExist:
            pass
