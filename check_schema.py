"""
Script to check database schema.
"""

import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_case_management.settings')
django.setup()

# Import models
from django.db import connection

def check_schema():
    """Check database schema."""
    print("Checking database schema...")
    
    # Check billing_invoice table
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(billing_invoice)")
        columns = cursor.fetchall()
        
        print("\nColumns in billing_invoice table:")
        for column in columns:
            print(f"  {column}")
        
        # Check billing_timeentry table
        cursor.execute("PRAGMA table_info(billing_timeentry)")
        columns = cursor.fetchall()
        
        print("\nColumns in billing_timeentry table:")
        for column in columns:
            print(f"  {column}")

if __name__ == "__main__":
    check_schema()
