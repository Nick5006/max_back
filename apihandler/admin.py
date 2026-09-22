from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "max_id", "name", "last_name", "is_jk", "is_staff", "is_active", "date_joined")
    list_filter = ("is_jk", "is_staff", "is_superuser", "is_active")
    search_fields = ("max_id", "name", "last_name", "id")
    ordering = ("-date_joined", "name")
    readonly_fields = ("id", "last_login", "date_joined")

    fieldsets = (
        ("Личное", {"fields": ("id", "max_id", "name", "last_name")}),
        ("Права", {"fields": ("is_active", "is_staff", "is_jk", "is_superuser", "groups", "user_permissions")}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("max_id", "name", "password1", "password2"),
        }),
    )