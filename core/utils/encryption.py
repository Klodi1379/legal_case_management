"""
Encryption utilities for the legal case management system.

This module provides encryption and decryption functions for sensitive data,
including document storage and personal information.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Check if encryption key is set in settings
if not hasattr(settings, 'ENCRYPTION_KEY'):
    raise ImproperlyConfigured(
        "ENCRYPTION_KEY must be set in settings for encryption to work. "
        "Generate a key with `python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"`"
    )

def get_encryption_key(salt=None):
    """
    Get or derive an encryption key.

    Args:
        salt: Optional salt for key derivation

    Returns:
        A Fernet key for encryption/decryption
    """
    if salt is None:
        # Use the key directly if no salt is provided
        try:
            key = settings.ENCRYPTION_KEY.encode()
            return Fernet(key)
        except Exception as e:
            raise ImproperlyConfigured(f"Invalid ENCRYPTION_KEY: {str(e)}")
    else:
        # Derive a key using the salt and the master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.ENCRYPTION_KEY.encode()))
        return Fernet(key)

def encrypt_file(file_data, salt=None):
    """
    Encrypt file data.

    Args:
        file_data: The file data to encrypt
        salt: Optional salt for key derivation

    Returns:
        Encrypted file data
    """
    if not file_data:
        return None

    # Get encryption key
    fernet = get_encryption_key(salt)

    # Encrypt the data
    if isinstance(file_data, str):
        file_data = file_data.encode()

    return fernet.encrypt(file_data)

def decrypt_file(encrypted_data, salt=None):
    """
    Decrypt file data.

    Args:
        encrypted_data: The encrypted file data
        salt: Optional salt used for encryption

    Returns:
        Decrypted file data
    """
    if not encrypted_data:
        return None

    # Get encryption key
    fernet = get_encryption_key(salt)

    # Decrypt the data
    return fernet.decrypt(encrypted_data)


def encrypt_text(text, salt=None):
    """
    Encrypt text data.

    Args:
        text: The text to encrypt
        salt: Optional salt for key derivation

    Returns:
        Encrypted text data as a base64-encoded string
    """
    if not text:
        return None

    # Get encryption key
    fernet = get_encryption_key(salt)

    # Ensure text is bytes
    if isinstance(text, str):
        text = text.encode('utf-8')

    # Encrypt the data
    encrypted_data = fernet.encrypt(text)

    # Return as base64 string for storage
    return base64.b64encode(encrypted_data).decode('ascii')


def decrypt_text(encrypted_text, salt=None):
    """
    Decrypt text data.

    Args:
        encrypted_text: The encrypted text as a base64-encoded string
        salt: Optional salt used for encryption

    Returns:
        Decrypted text as a string
    """
    if not encrypted_text:
        return None

    # Get encryption key
    fernet = get_encryption_key(salt)

    # Decode from base64
    encrypted_data = base64.b64decode(encrypted_text)

    # Decrypt the data
    decrypted_data = fernet.decrypt(encrypted_data)

    # Return as string
    return decrypted_data.decode('utf-8')
