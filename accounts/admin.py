from django.contrib import admin

# Register your models here.

# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from .models import User

# Register the User model in the admin site
admin.site.register(User)

