from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    User,
    Domik,
    Apartment,
    UserApartment,
    JKDomik,
    Appeal,
    AppealHistory
)


class UserApartmentInline(admin.TabularInline):
    model = UserApartment
    extra = 0
    autocomplete_fields = ("apartment",)
    fields = ("apartment", "role", "is_primary")
    verbose_name = "Квартира"
    verbose_name_plural = "Квартиры пользователя"


class JKDomikInline(admin.TabularInline):
    model = JKDomik
    extra = 0
    autocomplete_fields = ("domik",)
    verbose_name = "Дом (сотрудник УК)"
    verbose_name_plural = "Дома, которые обслуживает сотрудник"


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

    inlines = [UserApartmentInline, JKDomikInline]

class ApartmentInline(admin.TabularInline):
    model = Apartment
    extra = 0
    fields = ("number", "entrance")
    show_change_link = True


@admin.register(Domik)
class DomikAdmin(admin.ModelAdmin):
    list_display = ("address", "management_org", "fias_id", "apartments_count", "created_at")
    search_fields = ("address", "fias_id", "management_org")
    ordering = ("address",)
    readonly_fields = ("id", "created_at")
    inlines = [ApartmentInline]

    @admin.display(description="Квартир")
    def apartments_count(self, obj):
        return obj.apartments.count()


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ("__str__", "domik", "number", "entrance")
    list_filter = ("domik",)
    search_fields = ("number", "domik__address")
    autocomplete_fields = ("domik",)
    ordering = ("domik__address", "number")


@admin.register(UserApartment)
class UserApartmentAdmin(admin.ModelAdmin):
    list_display = ("user", "apartment", "role", "is_primary", "created_at")
    list_filter = ("role", "is_primary")
    search_fields = ("user__max_id", "user__name", "apartment__number", "apartment__domik__address")
    autocomplete_fields = ("user", "apartment")
    ordering = ("-is_primary", "user__name")


@admin.register(JKDomik)
class JKDomikAdmin(admin.ModelAdmin):
    list_display = ("user", "domik")
    search_fields = ("user__max_id", "user__name", "domik__address")
    autocomplete_fields = ("user", "domik")

class AppealHistoryInline(admin.TabularInline):
    model = AppealHistory
    extra = 0
    readonly_fields = ("status", "changed_by", "changed_at")


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "apartment", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description")
    inlines = [AppealHistoryInline]