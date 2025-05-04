# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, MFASetup

class MFASetupInline(admin.StackedInline):
    model = MFASetup
    can_delete = False
    verbose_name_plural = 'MFA Setup'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (MFASetupInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'has_mfa')
    list_filter = UserAdmin.list_filter + ('role', 'is_client', 'is_lawyer')
    fieldsets = UserAdmin.fieldsets + (
        ('Professional Information', {'fields': ('role', 'is_client', 'is_lawyer', 'phone_number',
                                               'mobile_number', 'address', 'bar_number',
                                               'practice_areas', 'hourly_rate', 'bio', 'profile_image')}),
    )

    def has_mfa(self, obj):
        try:
            return obj.mfa_setup.is_enabled
        except MFASetup.DoesNotExist:
            return False
    has_mfa.boolean = True
    has_mfa.short_description = 'MFA Enabled'

# Register the User model with the custom admin
admin.site.register(User, CustomUserAdmin)

# Register the MFASetup model
@admin.register(MFASetup)
class MFASetupAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_enabled', 'created_at', 'last_used')
    list_filter = ('is_enabled',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('secret_key', 'created_at', 'last_used')
