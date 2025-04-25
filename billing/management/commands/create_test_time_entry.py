from django.core.management.base import BaseCommand
from django.utils import timezone
from billing.models import TimeEntry
from cases.models import Case
from accounts.models import User
from datetime import date

class Command(BaseCommand):
    help = 'Creates a test time entry'

    def handle(self, *args, **options):
        # Get the first case
        case = Case.objects.first()
        if not case:
            self.stdout.write(self.style.ERROR("No cases found. Please create a case first."))
            return
        
        # Get the first user
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found. Please create a user first."))
            return
        
        # Create a time entry
        time_entry = TimeEntry(
            case=case,
            user=user,
            date=date.today(),
            hours=2.5,
            description="Test time entry",
            rate=150.00,
            is_billable=True
        )
        
        try:
            time_entry.save()
            self.stdout.write(self.style.SUCCESS(f"Time entry created successfully: {time_entry}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating time entry: {e}"))
