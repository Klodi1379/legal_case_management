# clients/admin.py
from django.contrib import admin
from .models import Client
from accounts.models import User

# Register the Client model in the admin site
admin.site.register(Client)
