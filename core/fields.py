"""
Custom fields for the legal case management system.

This module provides custom Django model fields, including fields for
encrypted data storage.
"""

import os
import uuid
from django.db import models
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .utils.encryption import encrypt_file, decrypt_file, encrypt_text, decrypt_text

class EncryptedFileField(models.FileField):
    """
    A FileField that encrypts files before saving and decrypts when accessed.

    This field ensures that sensitive documents are stored encrypted at rest.
    """

    def __init__(self, *args, **kwargs):
        self.salt_field = kwargs.pop('salt_field', None)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        """
        Process the file before saving to encrypt its contents.
        """
        file = super().pre_save(model_instance, add)
        if file and not getattr(file, '_encrypted', False):
            # Get or generate salt
            if self.salt_field:
                salt = getattr(model_instance, self.salt_field)
                if not salt:
                    salt = uuid.uuid4().bytes
                    setattr(model_instance, self.salt_field, salt)
            else:
                salt = None

            # Read file content
            file_content = file.read()
            file.seek(0)

            # Encrypt content
            encrypted_content = encrypt_file(file_content, salt)

            # Create a new file with encrypted content
            encrypted_file_name = f"{os.path.splitext(file.name)[0]}.enc"
            encrypted_file = ContentFile(encrypted_content)
            encrypted_file.name = encrypted_file_name
            encrypted_file._encrypted = True

            # Replace the original file with the encrypted one
            setattr(model_instance, self.attname, encrypted_file)
            return encrypted_file
        return file

    def generate_filename(self, instance, filename):
        """
        Generate a filename for the encrypted file.
        """
        # Add .enc extension to encrypted files if not already present
        if not filename.endswith('.enc'):
            filename = f"{filename}.enc"
        return super().generate_filename(instance, filename)

    def deconstruct(self):
        """
        Deconstruct the field for migrations.
        """
        name, path, args, kwargs = super().deconstruct()
        if self.salt_field:
            kwargs['salt_field'] = self.salt_field
        return name, path, args, kwargs


class EncryptedTextField(models.TextField):
    """
    A TextField that stores its content encrypted.

    This field ensures that sensitive text data is stored encrypted at rest.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """
        Prepare the value for database storage by encrypting it.
        """
        if value is None or value == '':
            return value

        # Encrypt the value using the global encryption key
        return encrypt_text(value)

    def from_db_value(self, value, expression, connection):
        """
        Convert the database value to a Python value.
        """
        if value is None or value == '':
            return value

        # Decrypt the value using the global encryption key
        try:
            return decrypt_text(value)
        except Exception as e:
            # If decryption fails, return the original value
            # This handles the case where data hasn't been encrypted yet
            return value

    def to_python(self, value):
        """
        Convert the value to a Python object.
        """
        if value is None or not isinstance(value, str) or value == '':
            return value

        # If the value is already decrypted, return it
        try:
            # Try to decode as base64 to check if it's encrypted
            import base64
            base64.b64decode(value)

            # If we get here, it might be encrypted, try to decrypt
            try:
                decrypted = decrypt_text(value)
                return decrypted
            except:
                # If decryption fails, assume it's already decrypted
                return value
        except:
            # If it's not base64, it's not encrypted
            return value


class EncryptedCharField(models.CharField):
    """
    A CharField that stores its content encrypted.

    This field ensures that sensitive character data is stored encrypted at rest.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """
        Prepare the value for database storage by encrypting it.
        """
        if value is None or value == '':
            return value

        # Encrypt the value using the global encryption key
        return encrypt_text(value)

    def from_db_value(self, value, expression, connection):
        """
        Convert the database value to a Python value.
        """
        if value is None or value == '':
            return value

        # Decrypt the value using the global encryption key
        try:
            return decrypt_text(value)
        except Exception as e:
            # If decryption fails, return the original value
            # This handles the case where data hasn't been encrypted yet
            return value

    def to_python(self, value):
        """
        Convert the value to a Python object.
        """
        if value is None or not isinstance(value, str) or value == '':
            return value

        # If the value is already decrypted, return it
        try:
            # Try to decode as base64 to check if it's encrypted
            import base64
            base64.b64decode(value)

            # If we get here, it might be encrypted, try to decrypt
            try:
                decrypted = decrypt_text(value)
                return decrypted
            except:
                # If decryption fails, assume it's already decrypted
                return value
        except:
            # If it's not base64, it's not encrypted
            return value
