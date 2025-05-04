# secure_clients/forms.py
from django import forms
from .models import SecureClientData, SecureContactData
from clients.models import Client, ClientContact


class SecureClientDataForm(forms.ModelForm):
    """Form for secure client data."""
    
    class Meta:
        model = SecureClientData
        exclude = ['client', 'created_at', 'updated_at']
        
    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.client:
            instance.client = self.client
        if commit:
            instance.save()
        return instance


class SecureContactDataForm(forms.ModelForm):
    """Form for secure contact data."""
    
    class Meta:
        model = SecureContactData
        exclude = ['contact', 'created_at', 'updated_at']
        
    def __init__(self, *args, **kwargs):
        self.contact = kwargs.pop('contact', None)
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.contact:
            instance.contact = self.contact
        if commit:
            instance.save()
        return instance


class CombinedClientForm(forms.ModelForm):
    """
    Combined form for client and secure client data.
    
    This form handles both the regular client data and the secure client data
    in a single form for a better user experience.
    """
    # Secure fields
    secure_first_name = forms.CharField(max_length=100, required=False, label="First Name")
    secure_last_name = forms.CharField(max_length=100, required=False, label="Last Name")
    secure_ssn_last_four = forms.CharField(max_length=4, required=False, label="Last 4 of SSN")
    secure_email = forms.EmailField(required=False, label="Email")
    secure_phone = forms.CharField(max_length=20, required=False, label="Phone")
    secure_mobile = forms.CharField(max_length=20, required=False, label="Mobile")
    secure_address_line1 = forms.CharField(max_length=255, required=False, label="Address Line 1")
    secure_address_line2 = forms.CharField(max_length=255, required=False, label="Address Line 2")
    secure_city = forms.CharField(max_length=100, required=False, label="City")
    secure_state = forms.CharField(max_length=100, required=False, label="State/Province")
    secure_postal_code = forms.CharField(max_length=20, required=False, label="Postal Code")
    secure_country = forms.CharField(max_length=100, required=False, label="Country")
    secure_company_name = forms.CharField(max_length=255, required=False, label="Company Name")
    secure_tax_id = forms.CharField(max_length=50, required=False, label="Tax ID")
    secure_notes = forms.CharField(widget=forms.Textarea, required=False, label="Notes")
    
    class Meta:
        model = Client
        fields = [
            'client_type', 'date_of_birth', 'industry',
        ]
        
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        
        # If we have an instance with secure data, populate the secure fields
        if instance and hasattr(instance, 'secure_data'):
            secure_data = instance.secure_data
            initial = kwargs.get('initial', {})
            initial.update({
                'secure_first_name': secure_data.first_name,
                'secure_last_name': secure_data.last_name,
                'secure_ssn_last_four': secure_data.ssn_last_four,
                'secure_email': secure_data.email,
                'secure_phone': secure_data.phone,
                'secure_mobile': secure_data.mobile,
                'secure_address_line1': secure_data.address_line1,
                'secure_address_line2': secure_data.address_line2,
                'secure_city': secure_data.city,
                'secure_state': secure_data.state,
                'secure_postal_code': secure_data.postal_code,
                'secure_country': secure_data.country,
                'secure_company_name': secure_data.company_name,
                'secure_tax_id': secure_data.tax_id,
                'secure_notes': secure_data.notes,
            })
            kwargs['initial'] = initial
            
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        client = super().save(commit=commit)
        
        if commit:
            # Get or create secure data
            secure_data, created = SecureClientData.objects.get_or_create(client=client)
            
            # Update secure data fields
            secure_data.first_name = self.cleaned_data.get('secure_first_name', '')
            secure_data.last_name = self.cleaned_data.get('secure_last_name', '')
            secure_data.ssn_last_four = self.cleaned_data.get('secure_ssn_last_four', '')
            secure_data.email = self.cleaned_data.get('secure_email', '')
            secure_data.phone = self.cleaned_data.get('secure_phone', '')
            secure_data.mobile = self.cleaned_data.get('secure_mobile', '')
            secure_data.address_line1 = self.cleaned_data.get('secure_address_line1', '')
            secure_data.address_line2 = self.cleaned_data.get('secure_address_line2', '')
            secure_data.city = self.cleaned_data.get('secure_city', '')
            secure_data.state = self.cleaned_data.get('secure_state', '')
            secure_data.postal_code = self.cleaned_data.get('secure_postal_code', '')
            secure_data.country = self.cleaned_data.get('secure_country', '')
            secure_data.company_name = self.cleaned_data.get('secure_company_name', '')
            secure_data.tax_id = self.cleaned_data.get('secure_tax_id', '')
            secure_data.notes = self.cleaned_data.get('secure_notes', '')
            
            # Save secure data
            secure_data.save()
            
        return client
