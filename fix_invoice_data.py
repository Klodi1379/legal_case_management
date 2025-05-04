"""
Script to fix invoice data issues.
"""

import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_case_management.settings')
django.setup()

# Import models
from django.db import connection
from django.contrib.auth import get_user_model
from billing.models import Invoice

User = get_user_model()

def fix_invoice_data():
    """Fix invoice data issues."""
    print("Fixing invoice data...")
    
    # Get the first user as a fallback
    default_user = User.objects.first()
    
    if not default_user:
        print("No users found. Please create a user first.")
        return
    
    print(f"Using default user: {default_user.username} (ID: {default_user.id})")
    
    # Use raw SQL to fix the data
    with connection.cursor() as cursor:
        # Check if there are invoices with invalid created_by_id
        cursor.execute("""
            SELECT id, created_by_id FROM billing_invoice
            WHERE created_by_id IS NULL OR created_by_id = 'created_by_id'
        """)
        invalid_invoices = cursor.fetchall()
        
        if invalid_invoices:
            print(f"Found {len(invalid_invoices)} invoices with invalid created_by_id")
            
            # Update the invoices with the default user
            cursor.execute("""
                UPDATE billing_invoice
                SET created_by_id = %s
                WHERE created_by_id IS NULL OR created_by_id = 'created_by_id'
            """, [default_user.id])
            
            print(f"Updated {len(invalid_invoices)} invoices with default user")
        else:
            print("No invoices with invalid created_by_id found")
    
    print("Invoice data fixed successfully")

if __name__ == "__main__":
    fix_invoice_data()
