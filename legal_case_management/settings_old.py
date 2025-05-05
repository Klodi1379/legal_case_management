"""
Django settings for legal_case_management project.

This file determines which settings module to use based on the environment.
"""
import os
import sys

# Determine which settings to use
environment = os.getenv('DJANGO_ENV', 'development')

if environment == 'production':
    from .settings.production import *
elif environment == 'development':
    from .settings.development import *
else:
    # Default to development
    from .settings.development import *

# For backward compatibility, if settings directory doesn't exist, use the base settings
# This is a temporary fix while migrating to the new structure
if not os.path.exists(os.path.join(os.path.dirname(__file__), 'settings')):
    from pathlib import Path
    
    # Build paths inside the project like this: BASE_DIR / 'subdir'.
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = "django-insecure-ex7g^#^%an=3b2x8j8#qt+gxlhvga%b67bl1yyh)cp6kl^lu^^"
    
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True
    
    ALLOWED_HOSTS = []
    
    # Application definition
    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "accounts",
        "billing",
        "cases",
        "clients",
        "documents",
        "portal",
        "core",
        "ai_services",
        "secure_clients",
    ]
    
    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        # "core.middleware.AuditLogMiddleware",  # Temporarily commented
    ]
    
    ROOT_URLCONF = "legal_case_management.urls"
    
    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [os.path.join(BASE_DIR, 'templates')],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        },
    ]
    
    WSGI_APPLICATION = "legal_case_management.wsgi.application"
    
    # Database
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    
    # Password validation
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]
    
    # Internationalization
    LANGUAGE_CODE = "en-us"
    TIME_ZONE = "UTC"
    USE_I18N = True
    USE_TZ = True
    
    # Static files (CSS, JavaScript, Images)
    STATIC_URL = "static/"
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_DIRS = [
        BASE_DIR / 'static',
    ]
    
    # Media files
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    
    # Default primary key field type
    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
    
    # Custom user model
    AUTH_USER_MODEL = 'accounts.User'
    
    # Authentication backends
    AUTHENTICATION_BACKENDS = [
        'accounts.auth.EmailOrUsernameModelBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]
    
    # Login settings
    LOGIN_URL = 'accounts:login'
    LOGIN_REDIRECT_URL = 'core:role_based_redirect'
    
    # Document encryption settings
    ENCRYPTION_KEY = "SCTLZTyFPe7C7WU4oqf1izZkKOodDeDzL_uMQcuiUbM="
    
    # AI Services settings
    ENABLE_AI_FEATURES = True
    DEFAULT_LLM_MODEL = 'gemma-3-12b-it-qat'
    DEFAULT_LLM_ENDPOINT = 'http://127.0.0.1:1234/v1/chat/completions'
