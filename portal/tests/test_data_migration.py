from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from io import StringIO

from clients.models import Client
from portal.models import PortalAccess

User = get_user_model()

class PortalDataMigrationTestCase(TestCase):
    """Test cases for portal data migration functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create client users without portal access
        self.client_user1 = User.objects.create_user(
            username='client1',
            email='client1@example.com',
            password='testpassword',
            is_client=True
        )
        
        self.client_user2 = User.objects.create_user(
            username='client2',
            email='client2@example.com',
            password='testpassword',
            is_client=True
        )
        
        # Create non-client user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpassword',
            is_client=False,
            is_staff=True
        )
        
        # Create client models
        self.client1 = Client.objects.create(
            user=self.client_user1,
            first_name='Client',
            last_name='One',
            email='client1@example.com'
        )
        
        self.client2 = Client.objects.create(
            user=self.client_user2,
            first_name='Client',
            last_name='Two',
            email='client2@example.com'
        )
        
        # Delete any automatically created portal access
        PortalAccess.objects.all().delete()
    
    def test_portal_access_signal_handler(self):
        """Test that portal access is created for new client users."""
        # Create a new client user
        new_client_user = User.objects.create_user(
            username='newclient',
            email='newclient@example.com',
            password='testpassword',
            is_client=True
        )
        
        # Check that portal access was created
        self.assertTrue(hasattr(new_client_user, 'portal_access'))
        self.assertTrue(new_client_user.portal_access.is_active)
    
    def test_update_user_to_client(self):
        """Test that portal access is created when user is updated to client."""
        # Update staff user to client
        self.staff_user.is_client = True
        self.staff_user.save()
        
        # Check that portal access was created
        self.assertTrue(hasattr(self.staff_user, 'portal_access'))
        self.assertTrue(self.staff_user.portal_access.is_active)
    
    def test_update_user_from_client(self):
        """Test that portal access is deactivated when user is no longer a client."""
        # First create portal access
        portal_access = PortalAccess.objects.create(
            user=self.client_user1,
            is_active=True
        )
        
        # Update user to not be a client
        self.client_user1.is_client = False
        self.client_user1.save()
        
        # Refresh portal access from database
        portal_access.refresh_from_db()
        
        # Check that portal access was deactivated
        self.assertFalse(portal_access.is_active)
