# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views_auth import CustomLoginView

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),

    # MFA
    path('mfa/setup/', views.mfa_setup, name='mfa_setup'),
    path('mfa/disable/', views.mfa_disable, name='mfa_disable'),
    path('mfa/backup-codes/', views.mfa_backup_codes, name='mfa_backup_codes'),
    path('mfa/verify/', views.mfa_verify, name='mfa_verify'),
]
