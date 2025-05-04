"""
Management command to set up portal access for existing client users.

This command creates PortalAccess objects for all client users who don't already have one.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from portal.models import PortalAccess, Notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Sets up portal access for existing client users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-welcome',
            action='store_true',
            help='Create welcome notifications for clients'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Setting up portal access for client users...'))
        
        create_welcome = options.get('create_welcome', False)
        
        # Set up portal access
        with transaction.atomic():
            access_count = self._setup_portal_access()
            
            if create_welcome:
                notification_count = self._create_welcome_notifications()
                self.stdout.write(self.style.SUCCESS(
                    f'Created {notification_count} welcome notifications'
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully set up portal access for {access_count} client users'
        ))
    
    def _setup_portal_access(self):
        """Set up portal access for client users."""
        count = 0
        
        # Get all client users
        client_users = User.objects.filter(is_client=True)
        
        for user in client_users:
            # Skip if portal access already exists
            if hasattr(user, 'portal_access'):
                continue
                
            # Create portal access
            portal_access = PortalAccess(
                user=user,
                is_active=True,
                last_login=timezone.now()
            )
            portal_access.save()
            count += 1
            
            if count % 10 == 0:
                self.stdout.write(f'Set up portal access for {count} users')
        
        return count
    
    def _create_welcome_notifications(self):
        """Create welcome notifications for clients with portal access."""
        count = 0
        
        # Get all active portal access
        portal_accesses = PortalAccess.objects.filter(is_active=True)
        
        for access in portal_accesses:
            # Create welcome notification
            Notification.objects.create(
                user=access.user,
                notification_type='OTHER',
                title='Welcome to the Client Portal',
                message='Welcome to your secure client portal. You can now access your cases, documents, and communicate with your legal team securely.',
                is_read=False
            )
            count += 1
        
        return count
