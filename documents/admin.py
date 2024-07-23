from django.contrib import admin

# Register your models here.
#lets register the model

from .models import Document
admin.site.register(Document)
