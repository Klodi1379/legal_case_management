# cases/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from clients.models import Client
import uuid

class PracticeArea(models.Model):
    """
    Legal practice areas for categorizing cases.
    """
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Practice Area')
        verbose_name_plural = _('Practice Areas')
        ordering = ['name']

class Court(models.Model):
    """
    Court information for legal cases.
    """
    name = models.CharField(_('Name'), max_length=200)
    jurisdiction = models.CharField(_('Jurisdiction'), max_length=100)
    address = models.TextField(_('Address'), blank=True)
    phone = models.CharField(_('Phone'), max_length=20, blank=True)
    website = models.URLField(_('Website'), blank=True)
    notes = models.TextField(_('Notes'), blank=True)

    def __str__(self):
        return f"{self.name} ({self.jurisdiction})"

    class Meta:
        verbose_name = _('Court')
        verbose_name_plural = _('Courts')
        ordering = ['jurisdiction', 'name']

class Case(models.Model):
    """
    Legal case/matter model with comprehensive tracking.
    """
    CASE_STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('PENDING', 'Pending'),
        ('DISCOVERY', 'Discovery'),
        ('TRIAL', 'Trial'),
        ('APPEAL', 'Appeal'),
        ('SETTLED', 'Settled'),
        ('CLOSED', 'Closed'),
        ('ARCHIVED', 'Archived'),
    ]
    CASE_TYPE_CHOICES = [
        ('CIVIL_LITIGATION', 'Civil Litigation'),
        ('CRIMINAL_DEFENSE', 'Criminal Defense'),
        ('CORPORATE', 'Corporate'),
        ('FAMILY', 'Family Law'),
        ('ESTATE', 'Estate Planning'),
        ('REAL_ESTATE', 'Real Estate'),
        ('INTELLECTUAL_PROPERTY', 'Intellectual Property'),
        ('IMMIGRATION', 'Immigration'),
        ('BANKRUPTCY', 'Bankruptcy'),
        ('PERSONAL_INJURY', 'Personal Injury'),
        ('EMPLOYMENT', 'Employment'),
        ('TAX', 'Tax'),
        ('OTHER', 'Other'),
    ]
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    # Basic case information
    title = models.CharField(_('Title'), max_length=255)
    case_number = models.CharField(_('Case Number'), max_length=50, unique=True)
    internal_reference = models.CharField(_('Internal Reference'), max_length=50, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='cases', verbose_name=_('Client'))
    practice_area = models.ForeignKey(PracticeArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='cases', verbose_name=_('Practice Area'))

    # Case details
    status = models.CharField(_('Status'), max_length=20, choices=CASE_STATUS_CHOICES, default='OPEN')
    case_type = models.CharField(_('Case Type'), max_length=30, choices=CASE_TYPE_CHOICES)
    description = models.TextField(_('Description'))
    priority = models.CharField(_('Priority'), max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')

    # Dates
    open_date = models.DateField(_('Open Date'), auto_now_add=True)
    close_date = models.DateField(_('Close Date'), null=True, blank=True)
    statute_of_limitations = models.DateField(_('Statute of Limitations'), null=True, blank=True)

    # Court information
    court = models.ForeignKey(Court, on_delete=models.SET_NULL, null=True, blank=True, related_name='cases', verbose_name=_('Court'))
    court_case_number = models.CharField(_('Court Case Number'), max_length=50, blank=True)
    judge = models.CharField(_('Judge'), max_length=100, blank=True)
    opposing_counsel = models.CharField(_('Opposing Counsel'), max_length=100, blank=True)

    # Financial information
    is_billable = models.BooleanField(_('Billable'), default=True)
    billing_method = models.CharField(_('Billing Method'), max_length=20, choices=[
        ('HOURLY', 'Hourly'),
        ('FLAT_FEE', 'Flat Fee'),
        ('CONTINGENCY', 'Contingency'),
        ('PRO_BONO', 'Pro Bono'),
    ], default='HOURLY')
    retainer_amount = models.DecimalField(_('Retainer Amount'), max_digits=10, decimal_places=2, null=True, blank=True)

    # Staff assignments
    assigned_attorney = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attorney_cases', verbose_name=_('Assigned Attorney'))
    assigned_paralegal = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='paralegal_cases', verbose_name=_('Assigned Paralegal'))

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cases', verbose_name=_('Created By'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.case_number})"

    def get_status_display_with_color(self):
        """Return status with appropriate color class for UI."""
        status_colors = {
            'OPEN': 'primary',
            'PENDING': 'secondary',
            'DISCOVERY': 'info',
            'TRIAL': 'warning',
            'APPEAL': 'danger',
            'SETTLED': 'success',
            'CLOSED': 'dark',
            'ARCHIVED': 'muted',
        }
        return {
            'status': self.get_status_display(),
            'color': status_colors.get(self.status, 'secondary')
        }

    def get_priority_display_with_color(self):
        """Return priority with appropriate color class for UI."""
        priority_colors = {
            'LOW': 'success',
            'MEDIUM': 'info',
            'HIGH': 'warning',
            'URGENT': 'danger',
        }
        return {
            'priority': self.get_priority_display(),
            'color': priority_colors.get(self.priority, 'secondary')
        }

    def is_active(self):
        """Check if case is currently active."""
        return self.status not in ['CLOSED', 'ARCHIVED']

    def days_since_opened(self):
        """Calculate days since case was opened."""
        from django.utils import timezone
        import datetime
        if self.open_date:
            today = timezone.now().date()
            return (today - self.open_date).days
        return 0

    class Meta:
        verbose_name = _('Case')
        verbose_name_plural = _('Cases')
        ordering = ['-open_date']
        permissions = [
            ('close_case', 'Can close a case'),
            ('reopen_case', 'Can reopen a case'),
            ('assign_case', 'Can assign a case to users'),
        ]

class CaseTeamMember(models.Model):
    """
    Team members assigned to a case.
    """
    ROLE_CHOICES = [
        ('LEAD_ATTORNEY', 'Lead Attorney'),
        ('ATTORNEY', 'Attorney'),
        ('PARALEGAL', 'Paralegal'),
        ('LEGAL_ASSISTANT', 'Legal Assistant'),
        ('CONSULTANT', 'Consultant'),
        ('OTHER', 'Other'),
    ]

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='team_members', verbose_name=_('Case'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='case_assignments', verbose_name=_('User'))
    role = models.CharField(_('Role'), max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(_('Active'), default=True)
    assigned_date = models.DateField(_('Assigned Date'), auto_now_add=True)
    notes = models.TextField(_('Notes'), blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} on {self.case}"

    class Meta:
        verbose_name = _('Case Team Member')
        verbose_name_plural = _('Case Team Members')
        unique_together = ['case', 'user', 'role']
        ordering = ['case', 'role']

class CaseNote(models.Model):
    """
    Notes related to a case.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='notes', verbose_name=_('Case'))
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('Author'))
    title = models.CharField(_('Title'), max_length=200, blank=True)
    content = models.TextField(_('Content'))
    is_private = models.BooleanField(_('Private'), default=False, help_text=_('Private notes are only visible to staff, not clients'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"Note by {self.author.get_full_name()} on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = _('Case Note')
        verbose_name_plural = _('Case Notes')
        ordering = ['-created_at']

class CaseEvent(models.Model):
    """
    Timeline events for a case.
    """
    EVENT_TYPE_CHOICES = [
        ('COURT_DATE', 'Court Date'),
        ('FILING', 'Filing'),
        ('DEADLINE', 'Deadline'),
        ('MEETING', 'Meeting'),
        ('DEPOSITION', 'Deposition'),
        ('COMMUNICATION', 'Communication'),
        ('OTHER', 'Other'),
    ]

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='events', verbose_name=_('Case'))
    title = models.CharField(_('Title'), max_length=200)
    event_type = models.CharField(_('Event Type'), max_length=20, choices=EVENT_TYPE_CHOICES)
    description = models.TextField(_('Description'), blank=True)
    date = models.DateField(_('Date'))
    time = models.TimeField(_('Time'), null=True, blank=True)
    location = models.CharField(_('Location'), max_length=200, blank=True)
    is_critical = models.BooleanField(_('Critical'), default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events', verbose_name=_('Created By'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.date}"

    class Meta:
        verbose_name = _('Case Event')
        verbose_name_plural = _('Case Events')
        ordering = ['date', 'time']


class ConflictCheck(models.Model):
    """
    Automated conflict of interest checking.

    Tracks conflict checks performed for cases to ensure ethical compliance
    and avoid potential conflicts of interest.
    """
    RESOLUTION_CHOICES = [
        ('NO_CONFLICT', 'No Conflict Found'),
        ('POTENTIAL_CONFLICT', 'Potential Conflict Identified'),
        ('CONFLICT_WAIVED', 'Conflict Waived'),
        ('CONFLICT_UNRESOLVED', 'Conflict Unresolved'),
        ('DECLINED', 'Representation Declined Due to Conflict'),
    ]

    SOURCE_CHOICES = [
        ('AUTOMATED', 'Automated Check'),
        ('MANUAL', 'Manual Check'),
        ('CLIENT_DISCLOSURE', 'Client Disclosure'),
        ('THIRD_PARTY', 'Third Party Information'),
    ]

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='conflict_checks', verbose_name=_('Case'))
    checked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performed_conflict_checks', verbose_name=_('Checked By'))
    check_date = models.DateTimeField(_('Check Date'), auto_now_add=True)

    # Check details
    check_source = models.CharField(_('Check Source'), max_length=20, choices=SOURCE_CHOICES, default='AUTOMATED')
    parties_checked = models.JSONField(_('Parties Checked'), default=list, help_text=_('List of parties checked for conflicts'))
    conflicts_found = models.BooleanField(_('Conflicts Found'), default=False)
    conflict_details = models.JSONField(_('Conflict Details'), null=True, blank=True, help_text=_('Details of any conflicts found'))

    # Resolution
    resolution_status = models.CharField(_('Resolution Status'), max_length=20, choices=RESOLUTION_CHOICES, default='NO_CONFLICT')
    resolution_notes = models.TextField(_('Resolution Notes'), blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='resolved_conflict_checks',
        verbose_name=_('Resolved By')
    )
    resolution_date = models.DateTimeField(_('Resolution Date'), null=True, blank=True)

    # Documentation
    waiver_document = models.FileField(_('Waiver Document'), upload_to='conflict_waivers/', null=True, blank=True)

    def __str__(self):
        return f"Conflict Check for {self.case} on {self.check_date.strftime('%Y-%m-%d')}"

    def perform_check(self):
        """
        Run automated conflict check algorithms.

        This method checks for conflicts against:
        1. Existing clients
        2. Opposing parties in other cases
        3. Related entities

        Returns:
            Dictionary with check results
        """
        # Get case client and related parties
        client = self.case.client

        # Initialize results
        results = {
            'conflicts_found': False,
            'potential_conflicts': [],
            'details': {}
        }

        # Check against opposing parties in other cases
        from clients.models import Client
        opposing_parties = []

        # Get all cases
        all_cases = Case.objects.exclude(id=self.case.id)

        # Check each case for potential conflicts
        for other_case in all_cases:
            # Skip cases for the same client
            if other_case.client_id == client.id:
                continue

            # Check if this client is opposing party in another case
            # This is a simplified check - in a real system, you would have a more
            # comprehensive opposing party tracking system
            if hasattr(other_case, 'opposing_parties'):
                for party in other_case.opposing_parties.all():
                    if party.name.lower() == client.name.lower():
                        opposing_parties.append({
                            'case_id': other_case.id,
                            'case_number': other_case.case_number,
                            'case_title': other_case.title,
                            'relationship': 'Opposing Party'
                        })

        if opposing_parties:
            results['conflicts_found'] = True
            results['potential_conflicts'].extend(opposing_parties)
            results['details']['opposing_parties'] = opposing_parties

        # Update the model with results
        self.conflicts_found = results['conflicts_found']
        self.conflict_details = results
        self.save()

        return results

    class Meta:
        verbose_name = _('Conflict Check')
        verbose_name_plural = _('Conflict Checks')
        ordering = ['-check_date']
        indexes = [
            models.Index(fields=['case', 'check_date']),
            models.Index(fields=['conflicts_found', 'resolution_status']),
        ]