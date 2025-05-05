"""
Management command to check security settings and configuration.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = 'Check security configuration and settings'

    def handle(self, *args, **options):
        self.stdout.write('Security Configuration Check')
        self.stdout.write('=' * 40)
        self.stdout.write('')
        
        # Track issues
        issues = []
        warnings = []
        
        # Check DEBUG setting
        self.stdout.write('1. Debug Mode:')
        if settings.DEBUG:
            issues.append('DEBUG is set to True - should be False in production')
            self.stdout.write(self.style.ERROR('   ✗ DEBUG is True (insecure for production)'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ DEBUG is False'))
        
        # Check SECRET_KEY
        self.stdout.write('\n2. Secret Key:')
        if 'django-insecure' in settings.SECRET_KEY or len(settings.SECRET_KEY) < 50:
            issues.append('SECRET_KEY appears to be insecure or too short')
            self.stdout.write(self.style.ERROR('   ✗ SECRET_KEY appears insecure'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ SECRET_KEY appears secure'))
        
        # Check ALLOWED_HOSTS
        self.stdout.write('\n3. Allowed Hosts:')
        if not settings.ALLOWED_HOSTS:
            warnings.append('ALLOWED_HOSTS is empty - should be configured for production')
            self.stdout.write(self.style.WARNING('   ! ALLOWED_HOSTS is empty'))
        else:
            self.stdout.write(self.style.SUCCESS(f'   ✓ ALLOWED_HOSTS configured: {settings.ALLOWED_HOSTS}'))
        
        # Check database
        self.stdout.write('\n4. Database:')
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite3' in db_engine:
            warnings.append('SQLite is being used - not recommended for production')
            self.stdout.write(self.style.WARNING('   ! Using SQLite (not recommended for production)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'   ✓ Using {db_engine}'))
        
        # Check encryption key
        self.stdout.write('\n5. Document Encryption:')
        if not settings.ENCRYPTION_KEY:
            issues.append('ENCRYPTION_KEY is not set')
            self.stdout.write(self.style.ERROR('   ✗ ENCRYPTION_KEY not configured'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ ENCRYPTION_KEY is configured'))
        
        # Check HTTPS settings
        self.stdout.write('\n6. HTTPS Settings:')
        if not settings.DEBUG:
            https_checks = {
                'SECURE_SSL_REDIRECT': settings.SECURE_SSL_REDIRECT,
                'SESSION_COOKIE_SECURE': settings.SESSION_COOKIE_SECURE,
                'CSRF_COOKIE_SECURE': settings.CSRF_COOKIE_SECURE,
                'SECURE_HSTS_SECONDS': settings.SECURE_HSTS_SECONDS > 0,
            }
            
            for setting, value in https_checks.items():
                if value:
                    self.stdout.write(self.style.SUCCESS(f'   ✓ {setting} is enabled'))
                else:
                    issues.append(f'{setting} is not enabled')
                    self.stdout.write(self.style.ERROR(f'   ✗ {setting} is not enabled'))
        else:
            self.stdout.write(self.style.WARNING('   ! HTTPS settings not enforced in DEBUG mode'))
        
        # Check middleware
        self.stdout.write('\n7. Security Middleware:')
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]
        
        for middleware in required_middleware:
            if middleware in settings.MIDDLEWARE:
                self.stdout.write(self.style.SUCCESS(f'   ✓ {middleware.split(".")[-1]} is enabled'))
            else:
                issues.append(f'{middleware} is not enabled')
                self.stdout.write(self.style.ERROR(f'   ✗ {middleware.split(".")[-1]} is not enabled'))
        
        # Check custom security middleware
        custom_middleware = [
            'core.middleware.security.SecurityHeadersMiddleware',
            'core.middleware.security.RateLimitMiddleware',
            'core.middleware.security.SessionSecurityMiddleware',
        ]
        
        for middleware in custom_middleware:
            if middleware in settings.MIDDLEWARE:
                self.stdout.write(self.style.SUCCESS(f'   ✓ {middleware.split(".")[-1]} is enabled'))
            else:
                warnings.append(f'{middleware} is not enabled')
                self.stdout.write(self.style.WARNING(f'   ! {middleware.split(".")[-1]} is not enabled'))
        
        # Check email settings
        self.stdout.write('\n8. Email Configuration:')
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            warnings.append('Using console email backend - configure SMTP for production')
            self.stdout.write(self.style.WARNING('   ! Using console email backend'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ Email backend configured'))
        
        # Check session settings
        self.stdout.write('\n9. Session Security:')
        session_checks = {
            'SESSION_COOKIE_HTTPONLY': getattr(settings, 'SESSION_COOKIE_HTTPONLY', False),
            'CSRF_COOKIE_HTTPONLY': getattr(settings, 'CSRF_COOKIE_HTTPONLY', False),
            'SESSION_EXPIRE_AT_BROWSER_CLOSE': settings.SESSION_EXPIRE_AT_BROWSER_CLOSE,
        }
        
        for setting, value in session_checks.items():
            if value:
                self.stdout.write(self.style.SUCCESS(f'   ✓ {setting} is enabled'))
            else:
                warnings.append(f'{setting} is not enabled')
                self.stdout.write(self.style.WARNING(f'   ! {setting} is not enabled'))
        
        # Check file permissions
        self.stdout.write('\n10. File Permissions:')
        if hasattr(settings, 'FILE_UPLOAD_PERMISSIONS'):
            self.stdout.write(self.style.SUCCESS(f'   ✓ FILE_UPLOAD_PERMISSIONS set to {oct(settings.FILE_UPLOAD_PERMISSIONS)}'))
        else:
            warnings.append('FILE_UPLOAD_PERMISSIONS not set')
            self.stdout.write(self.style.WARNING('   ! FILE_UPLOAD_PERMISSIONS not set'))
        
        # Summary
        self.stdout.write('\n' + '=' * 40)
        self.stdout.write('SUMMARY')
        self.stdout.write('=' * 40)
        
        if issues:
            self.stdout.write(self.style.ERROR(f'\nCritical Issues ({len(issues)}):'))
            for i, issue in enumerate(issues, 1):
                self.stdout.write(self.style.ERROR(f'  {i}. {issue}'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ No critical security issues found!'))
        
        if warnings:
            self.stdout.write(self.style.WARNING(f'\nWarnings ({len(warnings)}):'))
            for i, warning in enumerate(warnings, 1):
                self.stdout.write(self.style.WARNING(f'  {i}. {warning}'))
        
        if not issues and not warnings:
            self.stdout.write(self.style.SUCCESS('\n✓ Security configuration looks good!'))
        else:
            total = len(issues) + len(warnings)
            self.stdout.write(f'\nTotal issues found: {total}')
