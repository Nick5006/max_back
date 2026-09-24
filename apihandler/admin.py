from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    User,
    Domik,
    Apartment,
    UserApartment,
    JKDomik,
    Appeal,
    AppealHistory,
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
    verbose_name = "Дом"
    verbose_name_plural = "Дома, которые обслуживает сотрудник"


class ApartmentInline(admin.TabularInline):
    model = Apartment
    extra = 0
    fields = ("number", "entrance")
    show_change_link = True
    verbose_name = "Квартира"
    verbose_name_plural = "Квартиры дома"


class ResidentInline(admin.TabularInline):
    model = UserApartment
    extra = 0
    autocomplete_fields = ("user",)
    fields = ("user", "role", "is_primary")
    verbose_name = "Житель / собственник"
    verbose_name_plural = "Жильцы и собственники"


class JKDomikInlineInDomik(admin.TabularInline):
    model = JKDomik
    extra = 0
    autocomplete_fields = ("user",)
    verbose_name = "Сотрудник УК"
    verbose_name_plural = "Сотрудники УК"


class AppealHistoryInline(admin.TabularInline):
    model = AppealHistory
    extra = 0
    fields = ("status", "changed_by", "text", "changed_at")
    readonly_fields = ("status", "changed_by", "text", "changed_at")
    can_delete = False
    verbose_name = "Запись истории"
    verbose_name_plural = "История обращений"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "id", "max_id", "name", "last_name",
        "is_jk", "is_staff", "is_active", "date_joined",
    )
    list_filter = ("is_jk", "is_staff", "is_superuser", "is_active")
    search_fields = ("max_id", "name", "last_name", "id")
    ordering = ("-date_joined", "name")
    readonly_fields = ("id", "last_login", "date_joined")

    fieldsets = (
        ("Личное", {"fields": ("id", "max_id", "name", "last_name")}),
        ("Права", {
            "fields": (
                "is_active", "is_staff", "is_jk",
                "is_superuser", "groups", "user_permissions",
            ),
        }),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("max_id", "name", "password1", "password2"),
        }),
    )

    inlines = [UserApartmentInline, JKDomikInline]


@admin.register(Domik)
class DomikAdmin(admin.ModelAdmin):
    list_display = (
        "address", "management_org", "fias_id",
        "apartments_count", "jk_users_count", "created_at",
    )
    search_fields = ("address", "fias_id", "management_org")
    ordering = ("address",)
    readonly_fields = ("id", "created_at")
    inlines = [ApartmentInline, JKDomikInlineInDomik]

    @admin.display(description="Квартир")
    def apartments_count(self, obj):
        return obj.apartments.count()

    @admin.display(description="Сотрудников УК")
    def jk_users_count(self, obj):
        return obj.jk_users.count()


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ("number", "domik", "entrance", "residents_count")
    list_filter = ("domik",)
    search_fields = ("number", "domik__address")
    autocomplete_fields = ("domik",)
    ordering = ("domik__address", "number")
    inlines = [ResidentInline]

    @admin.display(description="Жильцов")
    def residents_count(self, obj):
        return obj.user_apartments.count()


@admin.register(UserApartment)
class UserApartmentAdmin(admin.ModelAdmin):
    list_display = ("user", "apartment", "role", "is_primary", "created_at")
    list_filter = ("role", "is_primary")
    search_fields = (
        "user__max_id", "user__name",
        "apartment__number", "apartment__domik__address",
    )
    autocomplete_fields = ("user", "apartment")
    ordering = ("-is_primary", "user__name")


@admin.register(JKDomik)
class JKDomikAdmin(admin.ModelAdmin):
    list_display = ("user", "domik")
    list_filter = ("domik",)
    search_fields = ("user__max_id", "user__name", "domik__address")
    autocomplete_fields = ("user", "domik")
    ordering = ("domik__address", "user__name")


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "author", "domik", "apartment",
        "status", "created_at", "updated_at",
    )
    list_filter = ("status", "domik", "created_at")
    search_fields = (
        "title", "description",
        "author__max_id", "author__name",
        "domik__address",
    )
    autocomplete_fields = ("author", "domik", "apartment")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [AppealHistoryInline]

    fieldsets = (
        ("Обращение", {
            "fields": ("id", "title", "description", "status"),
        }),
        ("Привязка", {
            "fields": ("author", "domik", "apartment"),
        }),
        ("Даты", {
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(AppealHistory)
class AppealHistoryAdmin(admin.ModelAdmin):
    list_display = ("appeal", "status", "changed_by", "changed_at")
    list_filter = ("status", "changed_at")
    search_fields = ("appeal__title", "changed_by__max_id", "changed_by__name")
    autocomplete_fields = ("appeal", "changed_by")
    ordering = ("-changed_at",)
    readonly_fields = ("appeal", "status", "changed_by", "text", "changed_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False