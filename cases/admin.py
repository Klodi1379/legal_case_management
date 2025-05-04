# cases/admin.py
from django.contrib import admin
from .models import Case, CaseNote, CaseEvent, ConflictCheck, PracticeArea, Court, CaseTeamMember

class CaseNoteInline(admin.TabularInline):
    model = CaseNote
    extra = 0

class CaseEventInline(admin.TabularInline):
    model = CaseEvent
    extra = 0

class ConflictCheckInline(admin.TabularInline):
    model = ConflictCheck
    extra = 0
    readonly_fields = ('check_date', 'conflicts_found')
    fields = ('check_source', 'checked_by', 'check_date', 'conflicts_found', 'resolution_status')

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'case_number', 'client', 'assigned_attorney', 'status', 'case_type', 'open_date')
    list_filter = ('status', 'case_type', 'open_date', 'priority')
    search_fields = ('title', 'case_number', 'client__user__username', 'assigned_attorney__username', 'description')
    inlines = [CaseNoteInline, CaseEventInline, ConflictCheckInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'case_number', 'internal_reference', 'client', 'practice_area')
        }),
        ('Case Details', {
            'fields': ('status', 'case_type', 'description', 'priority')
        }),
        ('Dates', {
            'fields': ('open_date', 'close_date', 'statute_of_limitations')
        }),
        ('Court Information', {
            'fields': ('court', 'court_case_number', 'judge', 'opposing_counsel')
        }),
        ('Financial Information', {
            'fields': ('is_billable', 'billing_method', 'retainer_amount')
        }),
        ('Staff Assignments', {
            'fields': ('assigned_attorney', 'assigned_paralegal')
        }),
    )

@admin.register(ConflictCheck)
class ConflictCheckAdmin(admin.ModelAdmin):
    list_display = ('case', 'checked_by', 'check_date', 'conflicts_found', 'resolution_status')
    list_filter = ('conflicts_found', 'resolution_status', 'check_source')
    search_fields = ('case__title', 'case__case_number', 'resolution_notes')
    readonly_fields = ('check_date', 'conflict_details')
    date_hierarchy = 'check_date'

@admin.register(PracticeArea)
class PracticeAreaAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'jurisdiction')
    list_filter = ('jurisdiction',)
    search_fields = ('name', 'jurisdiction', 'address')

@admin.register(CaseTeamMember)
class CaseTeamMemberAdmin(admin.ModelAdmin):
    list_display = ('case', 'user', 'role', 'is_active', 'assigned_date')
    list_filter = ('role', 'is_active')
    search_fields = ('case__title', 'user__username', 'notes')

@admin.register(CaseEvent)
class CaseEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'case', 'event_type', 'date', 'is_critical')
    list_filter = ('event_type', 'is_critical', 'date')
    search_fields = ('title', 'description', 'case__title')
    date_hierarchy = 'date'