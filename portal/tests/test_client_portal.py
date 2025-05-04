from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from clients.models import Client as ClientModel
from cases.models import Case
from portal.models import PortalAccess, MessageThread, Message, Notification, ClientTask
from documents.models import Document

User = get_user_model()

class ClientPortalTestCase(TestCase):
    """Test cases for the client portal functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create users with different roles
        self.client_user = User.objects.create_user(
            username='testclient',
            email='client@example.com',
            password='testpassword',
            is_client=True
        )
        
        self.attorney_user = User.objects.create_user(
            username='testattorney',
            email='attorney@example.com',
            password='testpassword',
            is_lawyer=True,
            role='ATTORNEY'
        )
        
        # Create client
        self.client_model = ClientModel.objects.create(
            user=self.client_user,
            first_name='Test',
            last_name='Client',
            email='client@example.com',
            phone='123-456-7890'
        )
        
        # Create case
        self.case = Case.objects.create(
            title='Test Case',
            client=self.client_model,
            assigned_attorney=self.attorney_user,
            status='OPEN',
            case_type='CIVIL',
            description='Test case description'
        )
        
        # Create portal access
        self.portal_access = PortalAccess.objects.create(
            user=self.client_user,
            is_active=True,
            last_login=timezone.now()
        )
        
        # Create message thread
        self.message_thread = MessageThread.objects.create(
            subject='Test Thread',
            case=self.case,
            created_by=self.client_user
        )
        self.message_thread.participants.add(self.client_user, self.attorney_user)
        
        # Create message
        self.message = Message.objects.create(
            thread=self.message_thread,
            sender=self.client_user,
            content='Test message content'
        )
        
        # Create client task
        self.task = ClientTask.objects.create(
            title='Test Task',
            description='Test task description',
            case=self.case,
            assigned_to=self.client_user,
            due_date=timezone.now() + timezone.timedelta(days=7),
            status='PENDING'
        )
        
        # Create notification
        self.notification = Notification.objects.create(
            user=self.client_user,
            notification_type='MESSAGE',
            title='Test Notification',
            message='Test notification message',
            related_object_id=self.message_thread.id,
            related_object_type='MessageThread'
        )
        
        # Create test client
        self.test_client = Client()
        
    def test_client_portal_access_allowed(self):
        """Test that client users can access the portal."""
        # Log in as client
        self.test_client.login(username='testclient', password='testpassword')
        
        # Try to access dashboard
        response = self.test_client.get(reverse('portal:dashboard'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal/dashboard.html')
        
    def test_client_portal_access_denied(self):
        """Test that non-client users cannot access the portal."""
        # Log in as attorney
        self.test_client.login(username='testattorney', password='testpassword')
        
        # Try to access dashboard
        response = self.test_client.get(reverse('portal:dashboard'))
        
        # Check response - should redirect to dashboard
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('core:dashboard'))
        
    def test_client_cases_view(self):
        """Test that client can view their cases."""
        # Log in as client
        self.test_client.login(username='testclient', password='testpassword')
        
        # Access cases view
        response = self.test_client.get(reverse('portal:cases'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal/cases.html')
        self.assertContains(response, 'Test Case')
        
    def test_client_case_detail_view(self):
        """Test that client can view case details."""
        # Log in as client
        self.test_client.login(username='testclient', password='testpassword')
        
        # Access case detail view
        response = self.test_client.get(
            reverse('portal:case_detail', kwargs={'case_id': self.case.id})
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal/case_detail.html')
        self.assertContains(response, 'Test Case')
        
    def test_client_messages_view(self):
        """Test that client can view their messages."""
        # Log in as client
        self.test_client.login(username='testclient', password='testpassword')
        
        # Access messages view
        response = self.test_client.get(reverse('portal:messages'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal/messages.html')
        self.assertContains(response, 'Test Thread')
        
    def test_message_thread_view(self):
        """Test that client can view a message thread."""
        # Log in as client
        self.test_client.login(username='testclient', password='testpassword')
        
        # Access message thread view
        response = self.test_client.get(
            reverse('portal:message_thread', kwargs={'thread_id': self.message_thread.id})
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test message content')
        
    def test_create_message(self):
        """Test that client can create a new message."""
        # Log in as client
        self.test_client.login(username='testclient', password='testpassword')
        
        # Post new message
        response = self.test_client.post(
            reverse('portal:message_thread', kwargs={'thread_id': self.message_thread.id}),
            {'content': 'New test message'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Check that message was created
        self.assertEqual(
            Message.objects.filter(thread=self.message_thread, content='New test message').count(),
            1
        )
        
    def test_create_message_thread(self):
        """Test that client can create a new message thread."""
        # Log in as client
        self.test_client.login(username='testclient', password='testpassword')
        
        # Post new thread
        response = self.test_client.post(
            reverse('portal:create_message'),
            {
                'subject': 'New Thread',
                'case': self.case.id,
                'message': 'Initial message'
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Check that thread was created
        thread = MessageThread.objects.filter(subject='New Thread').first()
        self.assertIsNotNone(thread)
        
        # Check that initial message was created
        self.assertEqual(
            Message.objects.filter(thread=thread, content='Initial message').count(),
            1
        )
        
    def test_notification_creation(self):
        """Test that notifications are created when messages are sent."""
        # Log in as client
        self.test_client.login(username='testclient', password='testpassword')
        
        # Count notifications before
        notification_count = Notification.objects.filter(
            user=self.attorney_user,
            notification_type='MESSAGE'
        ).count()
        
        # Post new message
        self.test_client.post(
            reverse('portal:message_thread', kwargs={'thread_id': self.message_thread.id}),
            {'content': 'Message that should create notification'}
        )
        
        # Check that notification was created for attorney
        new_notification_count = Notification.objects.filter(
            user=self.attorney_user,
            notification_type='MESSAGE'
        ).count()
        
        self.assertEqual(new_notification_count, notification_count + 1)
        
    def test_mark_message_as_read(self):
        """Test that viewing a message marks it as read."""
        # Log in as attorney
        self.test_client.login(username='testattorney', password='testpassword')
        
        # Check message is not read by attorney
        self.assertNotIn(self.attorney_user, self.message.read_by.all())
        
        # View message thread
        self.test_client.get(
            reverse('portal:message_thread', kwargs={'thread_id': self.message_thread.id})
        )
        
        # Refresh message from database
        self.message.refresh_from_db()
        
        # Check message is now read by attorney
        self.assertIn(self.attorney_user, self.message.read_by.all())
