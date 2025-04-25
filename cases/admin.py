# cases/admin.py
from django.contrib import admin
from .models import Case, CaseNote

class CaseNoteInline(admin.TabularInline):
    model = CaseNote
    extra = 0

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'case_number', 'client', 'assigned_lawyer', 'status', 'case_type', 'open_date')
    list_filter = ('status', 'case_type', 'open_date')
    search_fields = ('title', 'case_number', 'client__user__username', 'assigned_lawyer__username')
    inlines = [CaseNoteInline]