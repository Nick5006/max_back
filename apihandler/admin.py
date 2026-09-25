from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    User,
    Domik,
    Apartment,
    UserApartment,
    JKDomik,
    Appeal,
    AppealHistory,
)

admin.site.site_header = "Панель управления API"
admin.site.site_title = "API Admin"
admin.site.index_title = "Управление данными"


def badge(text, color):
    return format_html(
        '<span style="background:{};color:#fff;padding:2px 10px;'
        'border-radius:12px;font-size:11px;font-weight:600;'
        'display:inline-block;white-space:nowrap;">{}</span>',
        color,
        text,
    )


APPEAL_STATUS_COLORS = {
    Appeal.Status.NEW: "#2563eb",
    Appeal.Status.IN_PROGRESS: "#d97706",
    Appeal.Status.DONE: "#16a34a",
    Appeal.Status.REJECTED: "#dc2626",
}

ROLE_COLORS = {
    UserApartment.Role.RESIDENT: "#0ea5e9",
    UserApartment.Role.OWNER: "#7c3aed",
    UserApartment.Role.CHAIR: "#db2777",
}


class AppealStatusFilter(admin.SimpleListFilter):
    title = "статус обращения"
    parameter_name = "appeal_status"

    def lookups(self, request, model_admin):
        return Appeal.Status.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class RoleFilter(admin.SimpleListFilter):
    title = "роль"
    parameter_name = "role"

    def lookups(self, request, model_admin):
        return UserApartment.Role.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(role=self.value())
        return queryset


class UserApartmentInline(admin.TabularInline):
    model = UserApartment
    extra = 0
    autocomplete_fields = ("apartment",)
    fields = ("apartment", "role", "is_primary")
    verbose_name = "Квартира"
    verbose_name_plural = "Квартиры пользователя"
    classes = ("collapse",)


class JKDomikInline(admin.TabularInline):
    model = JKDomik
    extra = 0
    autocomplete_fields = ("domik",)
    verbose_name = "Дом"
    verbose_name_plural = "Дома, которые обслуживает сотрудник"
    classes = ("collapse",)


class ApartmentInline(admin.TabularInline):
    model = Apartment
    extra = 0
    fields = ("number", "entrance")
    show_change_link = True
    verbose_name = "Квартира"
    verbose_name_plural = "Квартиры дома"
    classes = ("collapse",)


class ResidentInline(admin.TabularInline):
    model = UserApartment
    extra = 0
    autocomplete_fields = ("user",)
    fields = ("user", "role", "is_primary")
    verbose_name = "Житель / собственник"
    verbose_name_plural = "Жильцы и собственники"
    classes = ("collapse",)


class JKDomikInlineInDomik(admin.TabularInline):
    model = JKDomik
    extra = 0
    autocomplete_fields = ("user",)
    verbose_name = "Сотрудник УК"
    verbose_name_plural = "Сотрудники УК"
    classes = ("collapse",)


class AppealHistoryInline(admin.TabularInline):
    model = AppealHistory
    extra = 0
    fields = ("status", "changed_by", "text", "changed_at")
    readonly_fields = ("status", "changed_by", "text", "changed_at")
    can_delete = False
    verbose_name = "Запись истории"
    verbose_name_plural = "История обращений"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "avatar", "max_id", "name", "last_name",
        "is_jk_badge", "is_staff_badge", "is_active_badge", "date_joined",
    )
    list_display_links = ("max_id", "name")
    list_filter = ("is_jk", "is_staff", "is_superuser", "is_active", "date_joined")
    search_fields = ("max_id", "name", "last_name", "id")
    ordering = ("-date_joined", "name")
    readonly_fields = ("id", "last_login", "date_joined", "avatar")
    list_per_page = 25
    date_hierarchy = "date_joined"

    fieldsets = (
        ("Личное", {"fields": ("id", "avatar", "max_id", "name", "last_name")}),
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

    @admin.display(description="")
    def avatar(self, obj):
        initial = (obj.name or obj.max_id or "?")[0].upper()
        return format_html(
            '<div style="width:32px;height:32px;border-radius:50%;'
            'background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;'
            'display:flex;align-items:center;justify-content:center;'
            'font-weight:600;font-size:14px;">{}</div>',
            initial,
        )

    @admin.display(description="УК", boolean=True)
    def is_jk_badge(self, obj):
        return obj.is_jk

    @admin.display(description="Персонал", boolean=True)
    def is_staff_badge(self, obj):
        return obj.is_staff

    @admin.display(description="Активен", boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active


@admin.register(Domik)
class DomikAdmin(admin.ModelAdmin):
    list_display = (
        "address", "management_org", "fias_id",
        "apartments_count", "jk_users_count", "appeals_count", "created_at",
    )
    search_fields = ("address", "fias_id", "management_org")
    ordering = ("address",)
    readonly_fields = ("id", "created_at")
    list_per_page = 25
    inlines = [ApartmentInline, JKDomikInlineInDomik]
    list_filter = ("management_org",)

    @admin.display(description="Квартир")
    def apartments_count(self, obj):
        return badge(str(obj.apartments.count()), "#0ea5e9")

    @admin.display(description="Сотрудников УК")
    def jk_users_count(self, obj):
        return badge(str(obj.jk_users.count()), "#7c3aed")

    @admin.display(description="Обращений")
    def appeals_count(self, obj):
        return badge(str(obj.appeals.count()), "#d97706")


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ("number", "domik_link", "entrance", "residents_count")
    list_filter = ("domik",)
    search_fields = ("number", "domik__address")
    autocomplete_fields = ("domik",)
    ordering = ("domik__address", "number")
    inlines = [ResidentInline]
    list_per_page = 50

    @admin.display(description="Дом", ordering="domik__address")
    def domik_link(self, obj):
        url = reverse("admin:apihandler_domik_change", args=[obj.domik.id])
        return format_html('<a href="{}">{}</a>', url, obj.domik.address)

    @admin.display(description="Жильцов")
    def residents_count(self, obj):
        return badge(str(obj.user_apartments.count()), "#0ea5e9")


@admin.register(UserApartment)
class UserApartmentAdmin(admin.ModelAdmin):
    list_display = ("user", "apartment", "role_badge", "is_primary", "created_at")
    list_filter = (RoleFilter, "is_primary", "created_at")
    search_fields = (
        "user__max_id", "user__name",
        "apartment__number", "apartment__domik__address",
    )
    autocomplete_fields = ("user", "apartment")
    ordering = ("-is_primary", "user__name")
    list_per_page = 50
    date_hierarchy = "created_at"

    @admin.display(description="Роль", ordering="role")
    def role_badge(self, obj):
        return badge(obj.get_role_display(), ROLE_COLORS.get(obj.role, "#64748b"))


@admin.register(JKDomik)
class JKDomikAdmin(admin.ModelAdmin):
    list_display = ("user", "domik")
    list_filter = ("domik",)
    search_fields = ("user__max_id", "user__name", "domik__address")
    autocomplete_fields = ("user", "domik")
    ordering = ("domik__address", "user__name")
    list_per_page = 50


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = (
        "short_id", "title", "author_link", "domik_link",
        "apartment_link", "status_badge", "created_at", "updated_at",
    )
    list_display_links = ("short_id", "title")
    list_filter = (AppealStatusFilter, "domik", "created_at")
    search_fields = (
        "title", "description",
        "author__max_id", "author__name",
        "domik__address",
    )
    autocomplete_fields = ("author", "domik", "apartment")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at", "status_badge")
    inlines = [AppealHistoryInline]
    list_per_page = 30
    date_hierarchy = "created_at"

    fieldsets = (
        ("Обращение", {
            "fields": ("id", "title", "description", "status", "status_badge"),
        }),
        ("Привязка", {
            "fields": ("author", "domik", "apartment"),
        }),
        ("Даты", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.display(description="ID", ordering="id")
    def short_id(self, obj):
        return str(obj.id)[:8]

    @admin.display(description="Автор", ordering="author__name")
    def author_link(self, obj):
        url = reverse("admin:apihandler_user_change", args=[obj.author.id])
        return format_html(
            '<a href="{}">{} {}</a>', url, obj.author.name, obj.author.last_name
        )

    @admin.display(description="Дом", ordering="domik__address")
    def domik_link(self, obj):
        url = reverse("admin:apihandler_domik_change", args=[obj.domik.id])
        return format_html('<a href="{}">{}</a>', url, obj.domik.address)

    @admin.display(description="Квартира")
    def apartment_link(self, obj):
        if not obj.apartment:
            return "—"
        url = reverse("admin:apihandler_apartment_change", args=[obj.apartment.id])
        return format_html('<a href="{}">кв. {}</a>', url, obj.apartment.number)

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        return badge(
            obj.get_status_display(),
            APPEAL_STATUS_COLORS.get(obj.status, "#64748b"),
        )


@admin.register(AppealHistory)
class AppealHistoryAdmin(admin.ModelAdmin):
    list_display = ("appeal_link", "status_badge", "changed_by", "changed_at")
    list_filter = ("status", "changed_at")
    search_fields = ("appeal__title", "changed_by__max_id", "changed_by__name")
    autocomplete_fields = ("appeal", "changed_by")
    ordering = ("-changed_at",)
    readonly_fields = ("appeal", "status", "changed_by", "text", "changed_at")
    list_per_page = 50
    date_hierarchy = "changed_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Обращение", ordering="appeal__title")
    def appeal_link(self, obj):
        url = reverse("admin:apihandler_appeal_change", args=[obj.appeal.id])
        return format_html('<a href="{}">{}</a>', url, obj.appeal.title)

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        return badge(
            obj.get_status_display(),
            APPEAL_STATUS_COLORS.get(obj.status, "#64748b"),
        )