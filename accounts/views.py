
# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from .forms import (
    UserRegistrationForm, UserUpdateForm,
    MFASetupForm, MFAVerificationForm, MFABackupCodeForm
)
from .models import User, MFASetup

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:profile')  # Redirect to profile page
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')  # Redirect to profile page
    else:
        form = UserUpdateForm(instance=request.user)

    # Check if user has MFA setup
    try:
        mfa_setup = request.user.mfa_setup
        has_mfa = True
        mfa_enabled = mfa_setup.is_enabled
    except MFASetup.DoesNotExist:
        has_mfa = False
        mfa_enabled = False

    return render(request, 'accounts/profile.html', {
        'form': form,
        'has_mfa': has_mfa,
        'mfa_enabled': mfa_enabled
    })


@login_required
def mfa_setup(request):
    """View for setting up MFA."""
    # Get or create MFA setup
    mfa_setup, created = MFASetup.objects.get_or_create(
        user=request.user,
        defaults={'secret_key': ''}
    )

    # Generate secret key if needed
    if not mfa_setup.secret_key:
        mfa_setup.generate_secret_key()

    if request.method == 'POST':
        form = MFAVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['verification_code']
            if mfa_setup.verify_code(code):
                # Enable MFA
                mfa_setup.is_enabled = True
                mfa_setup.save()

                # Generate backup codes
                backup_codes = mfa_setup.generate_backup_codes()

                messages.success(request, "Two-factor authentication has been enabled successfully.")
                return render(request, 'accounts/mfa_backup_codes.html', {
                    'backup_codes': backup_codes
                })
            else:
                messages.error(request, "Invalid verification code. Please try again.")
    else:
        form = MFAVerificationForm()

    # Generate QR code
    qr_code = mfa_setup.get_qr_code()

    return render(request, 'accounts/mfa_setup.html', {
        'form': form,
        'qr_code': qr_code,
        'secret_key': mfa_setup.secret_key
    })


@login_required
def mfa_disable(request):
    """View for disabling MFA."""
    try:
        mfa_setup = request.user.mfa_setup
    except MFASetup.DoesNotExist:
        messages.error(request, "Two-factor authentication is not set up.")
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = MFAVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['verification_code']
            if mfa_setup.verify_code(code):
                # Disable MFA
                mfa_setup.is_enabled = False
                mfa_setup.save()

                messages.success(request, "Two-factor authentication has been disabled.")
                return redirect('accounts:profile')
            else:
                messages.error(request, "Invalid verification code. Please try again.")
    else:
        form = MFAVerificationForm()

    return render(request, 'accounts/mfa_disable.html', {'form': form})


@login_required
def mfa_backup_codes(request):
    """View for generating new backup codes."""
    try:
        mfa_setup = request.user.mfa_setup
    except MFASetup.DoesNotExist:
        messages.error(request, "Two-factor authentication is not set up.")
        return redirect('accounts:profile')

    if not mfa_setup.is_enabled:
        messages.error(request, "Two-factor authentication is not enabled.")
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = MFAVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['verification_code']
            if mfa_setup.verify_code(code):
                # Generate new backup codes
                backup_codes = mfa_setup.generate_backup_codes()

                messages.success(request, "New backup codes have been generated.")
                return render(request, 'accounts/mfa_backup_codes.html', {
                    'backup_codes': backup_codes
                })
            else:
                messages.error(request, "Invalid verification code. Please try again.")
    else:
        form = MFAVerificationForm()

    return render(request, 'accounts/mfa_verify.html', {
        'form': form,
        'action': 'generate new backup codes'
    })


def mfa_verify(request):
    """View for verifying MFA during login."""
    # Get username from session
    username = request.session.get('mfa_user_username')
    if not username:
        return redirect('accounts:login')

    user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        form = MFAVerificationForm(request.POST)
        backup_form = MFABackupCodeForm(request.POST)

        # Check if verification code is provided
        if 'verification_code' in request.POST and form.is_valid():
            code = form.cleaned_data['verification_code']
            try:
                mfa_setup = user.mfa_setup
                if mfa_setup.verify_code(code):
                    # Update last used timestamp
                    mfa_setup.last_used = timezone.now()
                    mfa_setup.save()

                    # Log the user in
                    login(request, user)

                    # Clear session data
                    if 'mfa_user_username' in request.session:
                        del request.session['mfa_user_username']

                    # Redirect to the intended page or default
                    next_url = request.session.get('next', reverse('core:dashboard'))
                    if 'next' in request.session:
                        del request.session['next']

                    return HttpResponseRedirect(next_url)
                else:
                    messages.error(request, "Invalid verification code. Please try again.")
            except MFASetup.DoesNotExist:
                messages.error(request, "MFA is not set up for this account.")
                return redirect('accounts:login')

        # Check if backup code is provided
        elif 'backup_code' in request.POST and backup_form.is_valid():
            code = backup_form.cleaned_data['backup_code']
            try:
                mfa_setup = user.mfa_setup
                if mfa_setup.verify_backup_code(code):
                    # Log the user in
                    login(request, user)

                    # Clear session data
                    if 'mfa_user_username' in request.session:
                        del request.session['mfa_user_username']

                    # Redirect to the intended page or default
                    next_url = request.session.get('next', reverse('core:dashboard'))
                    if 'next' in request.session:
                        del request.session['next']

                    messages.warning(request, "You've used a backup code to log in. Only a limited number of backup codes are available.")
                    return HttpResponseRedirect(next_url)
                else:
                    messages.error(request, "Invalid backup code. Please try again.")
            except MFASetup.DoesNotExist:
                messages.error(request, "MFA is not set up for this account.")
                return redirect('accounts:login')
    else:
        form = MFAVerificationForm()
        backup_form = MFABackupCodeForm()

    return render(request, 'accounts/mfa_verify.html', {
        'form': form,
        'backup_form': backup_form,
        'username': username
    })
