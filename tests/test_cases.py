"""
Test cases for the cases app.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from clients.models import Client
from cases.models import Case, CaseNote, CaseEvent, PracticeArea, Court, ConflictCheck


class CaseModelTests(TestCase):
    """Test cases for the Case model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testlawyer',
            email='lawyer@test.com',
            password='TestPass123!',
            role='LAWYER'
        )
        
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            phone='123-456-7890',
            created_by=self.user
        )
        
        self.practice_area = PracticeArea.objects.create(
            name='Civil Litigation',
            description='Civil litigation cases'
        )
        
        self.court = Court.objects.create(
            name='Superior Court',
            jurisdiction='State',
            address='123 Court St'
        )
    
    def test_case_creation(self):
        """Test case creation with required fields."""
        case = Case.objects.create(
            title='Test Case',
            case_number='TC001',
            client=self.client_obj,
            case_type='CIVIL_LITIGATION',
            description='This is a test case',
            assigned_attorney=self.user,
            created_by=self.user
        )
        
        self.assertEqual(str(case), 'Test Case (TC001)')
        self.assertEqual(case.status, 'OPEN')
        self.assertEqual(case.priority, 'MEDIUM')
        self.assertTrue(case.is_active())
    
    def test_case_status_display(self):
        """Test case status display with color."""
        case = Case.objects.create(
            title='Test Case',
            case_number='TC002',
            client=self.client_obj,
            case_type='CIVIL_LITIGATION',
            description='This is a test case',
            status='DISCOVERY',
            assigned_attorney=self.user
        )
        
        status_display = case.get_status_display_with_color()
        self.assertEqual(status_display['status'], 'Discovery')
        self.assertEqual(status_display['color'], 'info')
    
    def test_case_priority_display(self):
        """Test case priority display with color."""
        case = Case.objects.create(
            title='Test Case',
            case_number='TC003',
            client=self.client_obj,
            case_type='CIVIL_LITIGATION',
            description='This is a test case',
            priority='HIGH',
            assigned_attorney=self.user
        )
        
        priority_display = case.get_priority_display_with_color()
        self.assertEqual(priority_display['priority'], 'High')
        self.assertEqual(priority_display['color'], 'warning')
    
    def test_days_since_opened(self):
        """Test days since case opened calculation."""
        case = Case.objects.create(
            title='Test Case',
            case_number='TC004',
            client=self.client_obj,
            case_type='CIVIL_LITIGATION',
            description='This is a test case',
            assigned_attorney=self.user
        )
        
        # Manually set open_date to 5 days ago
        five_days_ago = timezone.now().date() - timezone.timedelta(days=5)
        case.open_date = five_days_ago
        case.save()
        
        self.assertEqual(case.days_since_opened(), 5)


class CaseNoteTests(TestCase):
    """Test cases for the CaseNote model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testlawyer',
            email='lawyer@test.com',
            password='TestPass123!',
            role='LAWYER'
        )
        
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            created_by=self.user
        )
        
        self.case = Case.objects.create(
            title='Test Case',
            case_number='TC005',
            client=self.client_obj,
            case_type='CIVIL_LITIGATION',
            description='This is a test case',
            assigned_attorney=self.user
        )
    
    def test_case_note_creation(self):
        """Test case note creation."""
        note = CaseNote.objects.create(
            case=self.case,
            author=self.user,
            title='Important Note',
            content='This is an important note about the case.',
            is_private=False
        )
        
        self.assertIn('Note by', str(note))
        self.assertFalse(note.is_private)
    
    def test_private_case_note(self):
        """Test private case note creation."""
        note = CaseNote.objects.create(
            case=self.case,
            author=self.user,
            title='Private Note',
            content='This is a private note.',
            is_private=True
        )
        
        self.assertTrue(note.is_private)


class CaseEventTests(TestCase):
    """Test cases for the CaseEvent model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testlawyer',
            email='lawyer@test.com',
            password='TestPass123!',
            role='LAWYER'
        )
        
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            created_by=self.user
        )
        
        self.case = Case.objects.create(
            title='Test Case',
            case_number='TC006',
            client=self.client_obj,
            case_type='CIVIL_LITIGATION',
            description='This is a test case',
            assigned_attorney=self.user
        )
    
    def test_case_event_creation(self):
        """Test case event creation."""
        event_date = timezone.now().date() + timezone.timedelta(days=7)
        event = CaseEvent.objects.create(
            case=self.case,
            title='Court Hearing',
            event_type='COURT_DATE',
            description='Preliminary hearing',
            date=event_date,
            location='Courtroom 3A',
            is_critical=True,
            created_by=self.user
        )
        
        self.assertEqual(str(event), f'Court Hearing - {event_date}')
        self.assertTrue(event.is_critical)


class ConflictCheckTests(TestCase):
    """Test cases for the ConflictCheck model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testlawyer',
            email='lawyer@test.com',
            password='TestPass123!',
            role='LAWYER'
        )
        
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            created_by=self.user
        )
        
        self.case = Case.objects.create(
            title='Test Case',
            case_number='TC007',
            client=self.client_obj,
            case_type='CIVIL_LITIGATION',
            description='This is a test case',
            assigned_attorney=self.user
        )
    
    def test_conflict_check_creation(self):
        """Test conflict check creation."""
        conflict_check = ConflictCheck.objects.create(
            case=self.case,
            checked_by=self.user,
            check_source='MANUAL',
            parties_checked=['Party A', 'Party B'],
            conflicts_found=False,
            resolution_status='NO_CONFLICT'
        )
        
        self.assertIn('Conflict Check for', str(conflict_check))
        self.assertFalse(conflict_check.conflicts_found)
        self.assertEqual(conflict_check.resolution_status, 'NO_CONFLICT')
    
    def test_conflict_check_with_conflicts(self):
        """Test conflict check with conflicts found."""
        conflict_check = ConflictCheck.objects.create(
            case=self.case,
            checked_by=self.user,
            check_source='AUTOMATED',
            parties_checked=['Party A', 'Party B'],
            conflicts_found=True,
            conflict_details={'type': 'prior_representation', 'details': 'Represented Party B in 2022'},
            resolution_status='POTENTIAL_CONFLICT'
        )
        
        self.assertTrue(conflict_check.conflicts_found)
        self.assertEqual(conflict_check.resolution_status, 'POTENTIAL_CONFLICT')
        self.assertIn('type', conflict_check.conflict_details)


class CaseViewTests(TestCase):
    """Test cases for case views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()  # Django test client
        
        self.user = User.objects.create_user(
            username='testlawyer',
            email='lawyer@test.com',
            password='TestPass123!',
            role='LAWYER'
        )
        
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            created_by=self.user
        )
        
        self.case = Case.objects.create(
            title='Test Case',
            case_number='TC008',
            client=self.client_obj,
            case_type='CIVIL_LITIGATION',
            description='This is a test case',
            assigned_attorney=self.user
        )
    
    def test_case_list_view_requires_login(self):
        """Test that case list view requires authentication."""
        response = self.client.get(reverse('cases:case_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_case_list_view_authenticated(self):
        """Test case list view for authenticated users."""
        self.client.login(username='testlawyer', password='TestPass123!')
        response = self.client.get(reverse('cases:case_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Case')
    
    def test_case_detail_view(self):
        """Test case detail view."""
        self.client.login(username='testlawyer', password='TestPass123!')
        response = self.client.get(reverse('cases:case_detail', args=[self.case.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Case')
        self.assertContains(response, 'TC008')
