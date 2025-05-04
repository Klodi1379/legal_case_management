"""
Management command to encrypt client data.

This command encrypts sensitive client data for privacy and security.
"""

import uuid
import base64
from django.core.management.base import BaseCommand
from django.conf import settings
from cryptography.fernet import Fernet
from clients.models import Client, ClientContact
from core.utils.encryption import encrypt_text


class Command(BaseCommand):
    help = 'Encrypts sensitive client data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting client data encryption...'))
        
        # Process all clients
        clients_count = 0
        for client in Client.objects.all():
            # Generate salt if needed
            if not client.encryption_salt:
                client.encryption_salt = uuid.uuid4().bytes
                
            # Skip already encrypted data
            if self._is_encrypted(client.first_name):
                self.stdout.write(f'Client {client.id} already encrypted, skipping')
                continue
                
            # Encrypt individual client fields
            if client.first_name:
                client.first_name = encrypt_text(client.first_name)
            if client.last_name:
                client.last_name = encrypt_text(client.last_name)
            if client.ssn_last_four:
                client.ssn_last_four = encrypt_text(client.ssn_last_four)
            
            # Encrypt organization fields
            if client.company_name:
                client.company_name = encrypt_text(client.company_name)
            if client.tax_id:
                client.tax_id = encrypt_text(client.tax_id)
            
            # Encrypt contact information
            if client.email:
                client.email = encrypt_text(client.email)
            if client.phone:
                client.phone = encrypt_text(client.phone)
            if client.mobile:
                client.mobile = encrypt_text(client.mobile)
            if client.address_line1:
                client.address_line1 = encrypt_text(client.address_line1)
            if client.address_line2:
                client.address_line2 = encrypt_text(client.address_line2)
            if client.city:
                client.city = encrypt_text(client.city)
            if client.state:
                client.state = encrypt_text(client.state)
            if client.postal_code:
                client.postal_code = encrypt_text(client.postal_code)
            if client.country:
                client.country = encrypt_text(client.country)
            if client.notes:
                client.notes = encrypt_text(client.notes)
            
            # Save the client with encrypted data
            client.save()
            clients_count += 1
            
            if clients_count % 10 == 0:
                self.stdout.write(f'Encrypted {clients_count} clients')
        
        # Process all client contacts
        contacts_count = 0
        for contact in ClientContact.objects.all():
            # Generate salt if needed
            if not contact.encryption_salt:
                contact.encryption_salt = uuid.uuid4().bytes
                
            # Skip already encrypted data
            if self._is_encrypted(contact.first_name):
                self.stdout.write(f'Contact {contact.id} already encrypted, skipping')
                continue
            
            # Encrypt contact fields
            if contact.first_name:
                contact.first_name = encrypt_text(contact.first_name)
            if contact.last_name:
                contact.last_name = encrypt_text(contact.last_name)
            if contact.email:
                contact.email = encrypt_text(contact.email)
            if contact.phone:
                contact.phone = encrypt_text(contact.phone)
            if contact.mobile:
                contact.mobile = encrypt_text(contact.mobile)
            if contact.notes:
                contact.notes = encrypt_text(contact.notes)
            
            # Save the contact with encrypted data
            contact.save()
            contacts_count += 1
            
            if contacts_count % 10 == 0:
                self.stdout.write(f'Encrypted {contacts_count} contacts')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully encrypted {clients_count} clients and {contacts_count} contacts'))
    
    def _is_encrypted(self, value):
        """Check if a value is already encrypted."""
        if not value or not isinstance(value, str):
            return False
            
        # Try to decode as base64 to check if it's encrypted
        try:
            base64.b64decode(value)
            return True
        except:
            return False
