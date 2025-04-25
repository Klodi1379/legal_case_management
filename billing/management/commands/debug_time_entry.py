from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from billing.models import TimeEntry
from cases.models import Case
from accounts.models import User
from datetime import date
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Debug time entry creation'

    def add_arguments(self, parser):
        parser.add_argument('--case-id', type=int, help='Case ID')
        parser.add_argument('--user-id', type=int, help='User ID')

    def handle(self, *args, **options):
        # Enable query logging
        connection.force_debug_cursor = True
        
        try:
            # Get case
            case_id = options.get('case_id')
            if case_id:
                try:
                    case = Case.objects.get(id=case_id)
                    self.stdout.write(f"Using specified case: {case.id} - {case.title}")
                except Case.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Case with ID {case_id} does not exist"))
                    case = None
            else:
                case = Case.objects.first()
                if case:
                    self.stdout.write(f"Using first case: {case.id} - {case.title}")
                else:
                    self.stdout.write(self.style.ERROR("No cases found"))
                    return
            
            # Get user
            user_id = options.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    self.stdout.write(f"Using specified user: {user.id} - {user.username}")
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"User with ID {user_id} does not exist"))
                    user = None
            else:
                user = User.objects.first()
                if user:
                    self.stdout.write(f"Using first user: {user.id} - {user.username}")
                else:
                    self.stdout.write(self.style.ERROR("No users found"))
                    user = None
            
            # Create time entry
            self.stdout.write("Creating time entry...")
            time_entry = TimeEntry(
                case=case,
                user=user,
                date=date.today(),
                hours=2.5,
                description="Debug test time entry",
                rate=150.00,
                is_billable=True
            )
            
            # Print time entry details
            self.stdout.write(f"Time entry details:")
            self.stdout.write(f"  Case: {time_entry.case_id}")
            self.stdout.write(f"  User: {time_entry.user_id}")
            self.stdout.write(f"  Date: {time_entry.date}")
            self.stdout.write(f"  Hours: {time_entry.hours}")
            self.stdout.write(f"  Rate: {time_entry.rate}")
            
            # Save time entry
            time_entry.save()
            
            # Get the last executed query
            last_query = connection.queries[-1] if connection.queries else None
            self.stdout.write(f"SQL Query: {last_query}")
            
            self.stdout.write(self.style.SUCCESS(f"Time entry created successfully with ID: {time_entry.id}"))
            
        except Exception as e:
            # Log the error with the SQL
            last_query = connection.queries[-1] if connection.queries else None
            self.stdout.write(self.style.ERROR(f"SQL Query that failed: {last_query}"))
            self.stdout.write(self.style.ERROR(f"Error creating time entry: {str(e)}"))
            
            # Print all queries
            self.stdout.write("All executed queries:")
            for i, query in enumerate(connection.queries):
                self.stdout.write(f"{i+1}. {query}")
        
        finally:
            # Disable query logging
            connection.force_debug_cursor = False
