import os
import sys

print("=== PYTHON PATH ===")
for path in sys.path:
    print(path)
print("=================")

print("=== ENVIRONMENT VARIABLES ===")
for key, value in os.environ.items():
    if "DJANGO" in key:
        print(f"{key}: {value}")
print("=========================")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legal_case_management.settings")

print(f"Settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

import django
django.setup()

from django.conf import settings
import importlib

print("=== DJANGO SETTINGS DEBUG ===")
print(f"Settings module: {settings.SETTINGS_MODULE}")
print(f"Settings file: {importlib.import_module(settings.SETTINGS_MODULE).__file__}")
print(f"DEBUG: {settings.DEBUG}")
print(f"DEBUG type: {type(settings.DEBUG)}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"DATABASES: {settings.DATABASES}")
print("===========================")
