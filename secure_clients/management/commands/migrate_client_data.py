"""
Management command to migrate client data to secure storage.

This command copies sensitive client data to the secure client data models.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from clients.models import Client, ClientContact
from secure_clients.models import SecureClientData, SecureContactData


class Command(BaseCommand):
    help = 'Migrates sensitive client data to secure storage'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting client data migration...'))
        
        # Migrate client data
        with transaction.atomic():
            clients_count = self._migrate_clients()
            contacts_count = self._migrate_contacts()
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully migrated {clients_count} clients and {contacts_count} contacts to secure storage'
        ))
    
    def _migrate_clients(self):
        """Migrate client data to secure storage."""
        count = 0
        
        for client in Client.objects.all():
            # Skip if secure data already exists
            if hasattr(client, 'secure_data'):
                continue
                
            # Create secure client data
            secure_data = SecureClientData(
                client=client,
                first_name=client.first_name,
                last_name=client.last_name,
                ssn_last_four=client.ssn_last_four,
                email=client.email,
                phone=client.phone,
                mobile=client.mobile,
                address_line1=client.address_line1,
                address_line2=client.address_line2,
                city=client.city,
                state=client.state,
                postal_code=client.postal_code,
                country=client.country,
                company_name=client.company_name,
                tax_id=client.tax_id,
                notes=client.notes
            )
            secure_data.save()
            count += 1
            
            if count % 10 == 0:
                self.stdout.write(f'Migrated {count} clients')
        
        return count
    
    def _migrate_contacts(self):
        """Migrate contact data to secure storage."""
        count = 0
        
        for contact in ClientContact.objects.all():
            # Skip if secure data already exists
            if hasattr(contact, 'secure_data'):
                continue
                
            # Create secure contact data
            secure_data = SecureContactData(
                contact=contact,
                first_name=contact.first_name,
                last_name=contact.last_name,
                email=contact.email,
                phone=contact.phone,
                mobile=contact.mobile,
                notes=contact.notes
            )
            secure_data.save()
            count += 1
            
            if count % 10 == 0:
                self.stdout.write(f'Migrated {count} contacts')
        
        return count
