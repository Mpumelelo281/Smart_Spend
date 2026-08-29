from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AuditLog, StudentProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["email"]
    list_display = ["email", "role", "status", "mfa_enabled", "email_verified", "is_staff"]
    list_filter = ["role", "status", "mfa_enabled"]
    search_fields = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Role & status", {"fields": ("role", "status", "email_verified")}),
        ("MFA", {"fields": ("mfa_enabled",)}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role")}),)
    readonly_fields = ["mfa_enabled"]


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "campus", "allowance_amount", "disbursement_day"]
    search_fields = ["user__email", "campus"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    # Rule 8: append-only — no add/change/delete via admin, viewing only.
    list_display = ["created_at", "action", "actor", "target_type", "target_id", "ip_address"]
    list_filter = ["action"]
    search_fields = ["actor__email", "target_type", "target_id"]
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
