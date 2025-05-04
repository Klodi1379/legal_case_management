from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from cases.models import Case
import os
from django.utils import timezone
import uuid
from core.fields import EncryptedFileField

class DocumentCategory(models.Model):
    """
    Categories for organizing documents.
    """
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='subcategories', verbose_name=_('Parent Category'))

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

    class Meta:
        verbose_name = _('Document Category')
        verbose_name_plural = _('Document Categories')
        ordering = ['name']

class Document(models.Model):
    """
    Legal document model with comprehensive metadata.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('PLEADING', 'Pleading'),
        ('MOTION', 'Motion'),
        ('BRIEF', 'Brief'),
        ('CORRESPONDENCE', 'Correspondence'),
        ('CONTRACT', 'Contract'),
        ('AGREEMENT', 'Agreement'),
        ('EVIDENCE', 'Evidence'),
        ('DISCOVERY', 'Discovery'),
        ('DEPOSITION', 'Deposition'),
        ('EXHIBIT', 'Exhibit'),
        ('FORM', 'Form'),
        ('MEMO', 'Memo'),
        ('NOTE', 'Note'),
        ('REPORT', 'Report'),
        ('OTHER', 'Other'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('FINAL', 'Final'),
        ('FILED', 'Filed'),
        ('EXECUTED', 'Executed'),
        ('ARCHIVED', 'Archived'),
    ]

    # Basic document information
    title = models.CharField(_('Title'), max_length=255)
    document_type = models.CharField(_('Document Type'), max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='OTHER')
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='documents', verbose_name=_('Category'))
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    description = models.TextField(_('Description'), blank=True)

    # File information
    file = models.FileField(_('File'), upload_to='case_documents/')
    file_size = models.BigIntegerField(_('File Size'), null=True, blank=True, editable=False)
    file_type = models.CharField(_('File Type'), max_length=50, blank=True, editable=False)

    # Relationships
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents', verbose_name=_('Case'))

    # Metadata
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='uploaded_documents', verbose_name=_('Uploaded By'))
    uploaded_at = models.DateTimeField(_('Uploaded At'), auto_now_add=True)
    modified_at = models.DateTimeField(_('Modified At'), auto_now=True)
    document_date = models.DateField(_('Document Date'), null=True, blank=True,
                                    help_text=_('The date on the document itself'))

    # Access control
    is_private = models.BooleanField(_('Private'), default=False,
                                    help_text=_('Private documents are only visible to staff, not clients'))
    is_template = models.BooleanField(_('Template'), default=False,
                                     help_text=_('Document can be used as a template for generating new documents'))

    # Versioning
    version = models.PositiveIntegerField(_('Version'), default=1)
    is_latest_version = models.BooleanField(_('Latest Version'), default=True)
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='newer_version', verbose_name=_('Previous Version'))

    def __str__(self):
        return f"{self.title} (v{self.version})"

    def save(self, *args, **kwargs):
        # Set file size and type
        if self.file:
            self.file_size = self.file.size
            self.file_type = os.path.splitext(self.file.name)[1].lower()

        # If this is a new version of an existing document
        if self.previous_version and self.is_latest_version:
            # Mark the previous version as not the latest
            self.previous_version.is_latest_version = False
            self.previous_version.save()

        super().save(*args, **kwargs)

    def get_file_size_display(self):
        """Return human-readable file size."""
        if not self.file_size:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"

    def get_file_extension(self):
        """Return the file extension."""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ""

    def create_new_version(self, new_file, uploaded_by):
        """Create a new version of this document."""
        # Increment version number
        new_version_num = self.version + 1

        # Create new document instance
        new_doc = Document(
            title=self.title,
            document_type=self.document_type,
            category=self.category,
            status=self.status,
            description=self.description,
            file=new_file,
            case=self.case,
            uploaded_by=uploaded_by,
            document_date=self.document_date,
            is_private=self.is_private,
            is_template=self.is_template,
            version=new_version_num,
            is_latest_version=True,
            previous_version=self
        )

        # Save the new version
        new_doc.save()
        return new_doc

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['case', '-uploaded_at']),
            models.Index(fields=['document_type', '-uploaded_at']),
        ]

class DocumentTag(models.Model):
    """
    Tags for categorizing documents.
    """
    name = models.CharField(_('Name'), max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Document Tag')
        verbose_name_plural = _('Document Tags')
        ordering = ['name']

class DocumentTagged(models.Model):
    """
    Many-to-many relationship between documents and tags.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(DocumentTag, on_delete=models.CASCADE, related_name='documents')

    class Meta:
        unique_together = ['document', 'tag']
        verbose_name = _('Tagged Document')
        verbose_name_plural = _('Tagged Documents')

class DocumentTemplate(models.Model):
    """
    Templates for generating legal documents.
    """
    name = models.CharField(_('Name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    file = models.FileField(_('Template File'), upload_to='document_templates/')
    document_type = models.CharField(_('Document Type'), max_length=20, choices=Document.DOCUMENT_TYPE_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='created_templates', verbose_name=_('Created By'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    is_active = models.BooleanField(_('Active'), default=True)

    def __str__(self):
        return self.name


class SensitiveDocument(models.Model):
    """
    Encrypted document model for highly sensitive legal documents.

    This model uses encryption for the file content to ensure that
    sensitive documents are protected at rest.
    """
    SENSITIVITY_CHOICES = [
        ('CONFIDENTIAL', 'Confidential'),
        ('PRIVILEGED', 'Privileged'),
        ('RESTRICTED', 'Restricted'),
        ('TOP_SECRET', 'Top Secret'),
    ]

    # Basic document information
    title = models.CharField(_('Title'), max_length=255)
    document_type = models.CharField(_('Document Type'), max_length=20, choices=Document.DOCUMENT_TYPE_CHOICES, default='OTHER')
    sensitivity_level = models.CharField(_('Sensitivity Level'), max_length=20, choices=SENSITIVITY_CHOICES, default='CONFIDENTIAL')
    description = models.TextField(_('Description'), blank=True)

    # Encrypted file
    encryption_salt = models.BinaryField(_('Encryption Salt'), null=True, editable=False)
    file = EncryptedFileField(
        _('Encrypted File'),
        upload_to='encrypted_documents/',
        salt_field='encryption_salt'
    )
    file_size = models.BigIntegerField(_('File Size'), null=True, blank=True, editable=False)
    file_type = models.CharField(_('File Type'), max_length=50, blank=True, editable=False)

    # Relationships
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='sensitive_documents', verbose_name=_('Case'))
    parent_document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='sensitive_versions', verbose_name=_('Parent Document'))

    # Metadata
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='uploaded_sensitive_documents', verbose_name=_('Uploaded By'))
    uploaded_at = models.DateTimeField(_('Uploaded At'), auto_now_add=True)
    modified_at = models.DateTimeField(_('Modified At'), auto_now=True)

    # Access control
    authorized_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='accessible_sensitive_documents',
        verbose_name=_('Authorized Users'),
        blank=True
    )

    # Versioning
    version = models.PositiveIntegerField(_('Version'), default=1)
    is_latest_version = models.BooleanField(_('Latest Version'), default=True)
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='newer_version', verbose_name=_('Previous Version'))

    def __str__(self):
        return f"{self.title} (SENSITIVE)"

    def save(self, *args, **kwargs):
        # Set file size and type
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size
            self.file_type = os.path.splitext(self.file.name)[1].lower()

        # If this is a new version of an existing document
        if self.previous_version and self.is_latest_version:
            # Mark the previous version as not the latest
            self.previous_version.is_latest_version = False
            self.previous_version.save()

        super().save(*args, **kwargs)

    def get_file_size_display(self):
        """Return human-readable file size."""
        if not self.file_size:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"

    def get_file_extension(self):
        """Return the file extension."""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ""

    def create_new_version(self, new_file, uploaded_by):
        """Create a new version of this document."""
        # Increment version number
        new_version_num = self.version + 1

        # Create new document instance
        new_doc = SensitiveDocument(
            title=self.title,
            document_type=self.document_type,
            sensitivity_level=self.sensitivity_level,
            description=self.description,
            file=new_file,
            case=self.case,
            parent_document=self.parent_document,
            uploaded_by=uploaded_by,
            version=new_version_num,
            is_latest_version=True,
            previous_version=self
        )

        # Save the new version
        new_doc.save()

        # Copy authorized users
        for user in self.authorized_users.all():
            new_doc.authorized_users.add(user)

        return new_doc

    class Meta:
        verbose_name = _('Sensitive Document')
        verbose_name_plural = _('Sensitive Documents')
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['case', '-uploaded_at']),
            models.Index(fields=['sensitivity_level']),
        ]
        permissions = [
            ('view_any_sensitive_document', 'Can view any sensitive document'),
            ('upload_sensitive_document', 'Can upload sensitive documents'),
        ]

