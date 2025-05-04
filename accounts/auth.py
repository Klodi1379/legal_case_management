# accounts/auth.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend that allows login with either username or email.
    Also handles MFA verification.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Check if this is an MFA verification
        if 'mfa_user_id' in kwargs:
            try:
                return User.objects.get(id=kwargs['mfa_user_id'])
            except User.DoesNotExist:
                return None
        
        # Regular authentication with username/email and password
        if username is None or password is None:
            return None
        
        # Try to find a user that matches either username or email
        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
            
            # Check password
            if user.check_password(password):
                # Check if MFA is enabled
                try:
                    mfa_setup = user.mfa_setup
                    if mfa_setup.is_enabled:
                        # Store username in session for MFA verification
                        if request:
                            request.session['mfa_user_username'] = user.username
                            
                            # Store next URL if provided
                            if 'next' in request.GET:
                                request.session['next'] = request.GET['next']
                        
                        # Return None to prevent automatic login
                        return None
                except:
                    # If MFA is not set up, proceed with normal login
                    pass
                
                return user
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing attacks
            User().set_password(password)
        
        return None
