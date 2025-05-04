# accounts/views_auth.py
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse
from .models import MFASetup

class CustomLoginView(LoginView):
    """
    Custom login view that handles MFA redirection.
    """
    template_name = 'accounts/login.html'
    
    def form_valid(self, form):
        """
        Override form_valid to check for MFA and redirect if needed.
        """
        # Get the user
        user = form.get_user()
        
        # Check if MFA is enabled for this user
        try:
            mfa_setup = user.mfa_setup
            if mfa_setup.is_enabled:
                # Store username in session for MFA verification
                self.request.session['mfa_user_username'] = user.username
                
                # Store next URL if provided
                if 'next' in self.request.GET:
                    self.request.session['next'] = self.request.GET['next']
                
                # Redirect to MFA verification
                return redirect('accounts:mfa_verify')
        except MFASetup.DoesNotExist:
            # If MFA is not set up, proceed with normal login
            pass
        
        # Proceed with normal login
        return super().form_valid(form)
