from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import PasswordResetCode, User, UserProfile


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("firebase_uid", "full_name", "avatar_initials", "phone_number")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "password1", "password2"),
            },
        ),
    )
    list_display = ("email", "full_name", "firebase_uid", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("email",)
    search_fields = ("email", "full_name", "firebase_uid")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "family_name", "village", "clan", "updated_at")
    search_fields = ("user__email", "user__full_name", "family_name", "village", "clan")


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "code_type", "expires_at", "used_at", "attempts", "created_at")
    list_filter = ("code_type", "used_at", "expires_at", "created_at")
    search_fields = ("email",)
    readonly_fields = ("email", "code_hash", "code_type", "expires_at", "used_at", "attempts", "max_attempts")
