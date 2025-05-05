"""
Encryption utilities for handling sensitive data.
"""
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from core.exceptions import SecurityException


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    """

    def __init__(self):
        """Initialize encryption service with key from settings."""
        self.key = settings.ENCRYPTION_KEY
        if not self.key:
            raise SecurityException("Encryption key not configured")

        # Convert string key to bytes if needed
        if isinstance(self.key, str):
            self.key = self.key.encode()

        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.

        Args:
            data: String data to encrypt

        Returns:
            Encrypted data as base64 string
        """
        if not data:
            return data

        try:
            # Convert string to bytes
            data_bytes = data.encode()

            # Encrypt the data
            encrypted_bytes = self.fernet.encrypt(data_bytes)

            # Return as base64 string for storage
            return base64.b64encode(encrypted_bytes).decode()

        except Exception as e:
            raise SecurityException(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted string data.

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            Decrypted string data
        """
        if not encrypted_data:
            return encrypted_data

        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())

            # Decrypt the data
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)

            # Return as string
            return decrypted_bytes.decode()

        except Exception as e:
            raise SecurityException(f"Decryption failed: {str(e)}")


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    This should be used to generate keys for new deployments.
    The key should be stored securely and never committed to version control.

    Returns:
        Base64-encoded encryption key
    """
    return Fernet.generate_key().decode()


def derive_key_from_password(password: str, salt: bytes = None) -> tuple[str, bytes]:
    """
    Derive an encryption key from a password using PBKDF2.

    Args:
        password: Password to derive key from
        salt: Salt for key derivation (generated if not provided)

    Returns:
        Tuple of (base64-encoded key, salt)
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

    return key.decode(), salt


# Global encryption service instance
encryption_service = None

def get_encryption_service() -> EncryptionService:
    """
    Get or create the global encryption service instance.

    Returns:
        EncryptionService instance
    """
    global encryption_service

    if encryption_service is None:
        encryption_service = EncryptionService()

    return encryption_service


def encrypt_text(text: str) -> str:
    """
    Encrypt text using the global encryption service.

    Args:
        text: Text to encrypt

    Returns:
        Encrypted text as base64 string
    """
    if not text:
        return text

    service = get_encryption_service()
    return service.encrypt(text)


def decrypt_text(encrypted_text: str) -> str:
    """
    Decrypt text using the global encryption service.

    Args:
        encrypted_text: Encrypted text to decrypt

    Returns:
        Decrypted text
    """
    if not encrypted_text:
        return encrypted_text

    service = get_encryption_service()
    return service.decrypt(encrypted_text)


def encrypt_file(file_content: bytes, salt: bytes = None) -> bytes:
    """
    Encrypt file content.

    Args:
        file_content: File content as bytes
        salt: Optional salt for encryption

    Returns:
        Encrypted file content as bytes
    """
    if not file_content:
        return file_content

    # Use the encryption service for now
    # In a real implementation, we might want to use a different approach for files
    service = get_encryption_service()

    # Convert to base64 string first (since encrypt expects string)
    content_b64 = base64.b64encode(file_content).decode()

    # Encrypt and convert back to bytes
    encrypted = service.encrypt(content_b64)
    return encrypted.encode()


def decrypt_file(encrypted_content: bytes, salt: bytes = None) -> bytes:
    """
    Decrypt file content.

    Args:
        encrypted_content: Encrypted file content as bytes
        salt: Optional salt used for encryption

    Returns:
        Decrypted file content as bytes
    """
    if not encrypted_content:
        return encrypted_content

    # Use the encryption service
    service = get_encryption_service()

    # Decrypt the content (convert bytes to string first)
    decrypted_b64 = service.decrypt(encrypted_content.decode())

    # Convert from base64 back to bytes
    return base64.b64decode(decrypted_b64)
