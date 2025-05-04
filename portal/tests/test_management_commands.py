from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone
from io import StringIO

from clients.models import Client
from cases.models import Case
from portal.models import PortalAccess, ClientTask, Notification

User = get_user_model()

class ManagementCommandsTestCase(TestCase):
    """Test cases for portal management commands."""
    
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
        
        # Create attorney user
        self.attorney_user = User.objects.create_user(
            username='attorney',
            email='attorney@example.com',
            password='testpassword',
            is_lawyer=True,
            role='ATTORNEY'
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
        
        # Create case
        self.case = Case.objects.create(
            title='Test Case',
            client=self.client1,
            assigned_attorney=self.attorney_user,
            status='OPEN',
            case_type='CIVIL',
            description='Test case description',
            open_date=timezone.now() - timezone.timedelta(days=10)
        )
        
        # Delete any automatically created portal access
        PortalAccess.objects.all().delete()
    
    def test_setup_client_portal_access_command(self):
        """Test the setup_client_portal_access command."""
        # Call the command
        out = StringIO()
        call_command('setup_client_portal_access', stdout=out)
        
        # Check output
        self.assertIn('Successfully set up portal access for', out.getvalue())
        
        # Check that portal access was created
        self.assertEqual(PortalAccess.objects.count(), 2)
        self.assertTrue(PortalAccess.objects.filter(user=self.client_user1).exists())
        self.assertTrue(PortalAccess.objects.filter(user=self.client_user2).exists())
    
    def test_setup_client_portal_access_with_welcome(self):
        """Test the setup_client_portal_access command with welcome notifications."""
        # Call the command with create-welcome option
        out = StringIO()
        call_command('setup_client_portal_access', '--create-welcome', stdout=out)
        
        # Check output
        self.assertIn('Successfully set up portal access for', out.getvalue())
        self.assertIn('Created', out.getvalue())
        self.assertIn('welcome notifications', out.getvalue())
        
        # Check that notifications were created
        self.assertEqual(Notification.objects.count(), 2)
        self.assertTrue(Notification.objects.filter(
            user=self.client_user1,
            title='Welcome to the Client Portal'
        ).exists())
        self.assertTrue(Notification.objects.filter(
            user=self.client_user2,
            title='Welcome to the Client Portal'
        ).exists())
    
    def test_setup_client_tasks_command(self):
        """Test the setup_client_tasks command."""
        # Call the command
        out = StringIO()
        call_command('setup_client_tasks', stdout=out)
        
        # Check output
        self.assertIn('Successfully created', out.getvalue())
        
        # Check that tasks were created
        self.assertTrue(ClientTask.objects.filter(
            case=self.case,
            title='Provide Additional Information'
        ).exists())
    
    def test_setup_client_tasks_with_notify(self):
        """Test the setup_client_tasks command with notifications."""
        # Call the command with notify option
        out = StringIO()
        call_command('setup_client_tasks', '--notify', stdout=out)
        
        # Check output
        self.assertIn('Successfully created', out.getvalue())
        
        # Check that tasks were created
        task = ClientTask.objects.filter(
            case=self.case,
            title='Provide Additional Information'
        ).first()
        self.assertIsNotNone(task)
        
        # Check that notifications were created
        self.assertTrue(Notification.objects.filter(
            user=self.client_user1,
            notification_type='TASK',
            related_object_id=task.id,
            related_object_type='ClientTask'
        ).exists())
    
    def test_setup_client_tasks_for_specific_case(self):
        """Test the setup_client_tasks command for a specific case."""
        # Call the command with case-id option
        out = StringIO()
        call_command('setup_client_tasks', f'--case-id={self.case.id}', stdout=out)
        
        # Check output
        self.assertIn(f'Created', out.getvalue())
        self.assertIn(f'tasks for case {self.case.title}', out.getvalue())
        
        # Check that tasks were created
        self.assertTrue(ClientTask.objects.filter(
            case=self.case,
            title='Provide Additional Information'
        ).exists())
