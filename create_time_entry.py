import os
import django
import sys
from datetime import date

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_case_management.settings')
django.setup()

# Import models
from billing.models import TimeEntry
from cases.models import Case
from accounts.models import User

def create_time_entry():
    # Get the first case
    case = Case.objects.first()
    if not case:
        print("No cases found. Please create a case first.")
        return
    
    # Get the first user
    user = User.objects.first()
    if not user:
        print("No users found. Please create a user first.")
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
        print(f"Time entry created successfully: {time_entry}")
    except Exception as e:
        print(f"Error creating time entry: {e}")

if __name__ == "__main__":
    create_time_entry()
