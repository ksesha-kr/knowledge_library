from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, RegistrationKey


class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff']
    list_filter = ['role', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'registration_key')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'registration_key')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(RegistrationKey)
class RegistrationKeyAdmin(admin.ModelAdmin):
    list_display = ['key_short', 'role', 'created_by', 'created_at', 'expires_at', 'uses', 'max_uses', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['key', 'note']

    def key_short(self, obj):
        return f"{obj.key[:12]}..."

    key_short.short_description = 'Ключ'