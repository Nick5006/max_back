from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count

from .models import (
    User,
    Domik,
    Apartment,
    UserApartment,
    ManagementOrganization,
    Appeal,
    AppealHistory,
    Poll,
    Choice,
    Vote,
    CapitalRepair,
    CapitalRepairWork,
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


class DomikInlineInOrg(admin.TabularInline):
    model = Domik
    fk_name = "management_org"
    extra = 0
    fields = ("address", "fias_id")
    show_change_link = True
    verbose_name = "Дом"
    verbose_name_plural = "Дома под управлением"
    classes = ("collapse",)


class UKStaffInline(admin.TabularInline):
    model = User
    fk_name = "management_org"
    extra = 0
    fields = ("max_id", "name", "last_name", "is_jk", "is_active")
    show_change_link = True
    verbose_name = "Сотрудник УК"
    verbose_name_plural = "Сотрудники УК"
    classes = ("collapse",)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0
    fields = ("order", "text", "votes_count_display")
    readonly_fields = ("votes_count_display",)
    verbose_name = "Вариант ответа"
    verbose_name_plural = "Варианты ответа"
    ordering = ("order",)

    @admin.display(description="Голосов")
    def votes_count_display(self, obj):
        if obj.pk is None:
            return "—"
        return badge(str(obj.votes.count()), "#0ea5e9")


class PollAdmin(admin.ModelAdmin):
    list_display = (
        "title", "author_link", "domik_link",
        "is_active_badge", "choices_count", "votes_count",
        "created_at",
    )
    list_display_links = ("title",)
    list_filter = ("is_active", "created_at", "domik__management_org")
    search_fields = (
        "title", "description",
        "author__max_id", "author__name",
        "domik__address",
    )
    autocomplete_fields = ("author", "domik")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "votes_count", "choices_count")
    inlines = [ChoiceInline]
    list_per_page = 30
    date_hierarchy = "created_at"

    fieldsets = (
        ("Опрос", {
            "fields": ("id", "title", "description", "is_active"),
        }),
        ("Привязка", {
            "fields": ("author", "domik"),
        }),
        ("Статистика", {
            "fields": ("choices_count", "votes_count"),
        }),
        ("Даты", {
            "fields": ("created_at",),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("author", "domik", "domik__management_org")
            .annotate(_choices_count=Count("choices", distinct=True))
            .annotate(_votes_count=Count("votes", distinct=True))
        )

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

    @admin.display(description="Активен", boolean=True, ordering="is_active")
    def is_active_badge(self, obj):
        return obj.is_active

    @admin.display(description="Вариантов", ordering="_choices_count")
    def choices_count(self, obj):
        return badge(str(obj._choices_count), "#0ea5e9")

    @admin.display(description="Голосов", ordering="_votes_count")
    def votes_count(self, obj):
        return badge(str(obj._votes_count), "#7c3aed")


class VoteAdmin(admin.ModelAdmin):
    list_display = ("poll_link", "choice", "user_link", "created_at")
    list_filter = ("created_at", "poll")
    search_fields = (
        "poll__title",
        "choice__text",
        "user__max_id", "user__name",
    )
    autocomplete_fields = ("poll", "user")   # ← убрали "choice"
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at")
    list_per_page = 50
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Опрос", ordering="poll__title")
    def poll_link(self, obj):
        url = reverse("admin:apihandler_poll_change", args=[obj.poll.id])
        return format_html('<a href="{}">{}</a>', url, obj.poll.title)

    @admin.display(description="Пользователь", ordering="user__name")
    def user_link(self, obj):
        url = reverse("admin:apihandler_user_change", args=[obj.user.id])
        return format_html(
            '<a href="{}">{} {}</a>', url, obj.user.name, obj.user.last_name
        )

@admin.register(ManagementOrganization)
class ManagementOrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "inn", "domiks_count", "staff_count", "created_at")
    search_fields = ("name", "inn")
    readonly_fields = ("id", "created_at")
    ordering = ("name",)
    list_per_page = 50
    inlines = [DomikInlineInOrg, UKStaffInline]

    @admin.display(description="Домов")
    def domiks_count(self, obj):
        return badge(str(obj.domiks.count()), "#0ea5e9")

    @admin.display(description="Сотрудников")
    def staff_count(self, obj):
        return badge(str(obj.jk_users.count()), "#7c3aed")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "avatar", "max_id", "name", "last_name",
        "management_org", "is_jk_badge", "is_staff_badge",
        "is_active_badge", "date_joined",
    )
    list_display_links = ("max_id", "name")
    list_filter = (
        "is_jk", "is_staff", "is_superuser", "is_active",
        "management_org", "date_joined",
    )
    search_fields = ("max_id", "name", "last_name", "id", "management_org__name")
    ordering = ("-date_joined", "name")
    readonly_fields = ("id", "last_login", "date_joined", "avatar")
    autocomplete_fields = ("management_org",)
    list_per_page = 25
    date_hierarchy = "date_joined"

    fieldsets = (
        ("Личное", {"fields": ("id", "avatar", "max_id", "name", "last_name")}),
        ("Права", {
            "fields": (
                "is_active", "is_staff", "is_jk", "management_org",
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

    inlines = [UserApartmentInline]

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
        "apartments_count", "appeals_count", "polls_count", "created_at",
    )
    search_fields = ("address", "fias_id", "management_org__name")
    ordering = ("address",)
    readonly_fields = ("id", "created_at")
    list_per_page = 25
    autocomplete_fields = ("management_org",)
    inlines = [ApartmentInline]
    list_filter = ("management_org",)

    @admin.display(description="Квартир")
    def apartments_count(self, obj):
        return badge(str(obj.apartments.count()), "#0ea5e9")

    @admin.display(description="Обращений")
    def appeals_count(self, obj):
        return badge(str(obj.appeals.count()), "#d97706")

    @admin.display(description="Опросов")
    def polls_count(self, obj):
        return badge(str(obj.polls.count()), "#7c3aed")


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

class CapitalRepairWorkInline(admin.TabularInline):
    model = CapitalRepairWork
    extra = 0
    fields = ("work_type", "planned_year", "status", "cost", "contractor")
    verbose_name = "Работа"
    verbose_name_plural = "Программа работ"
    classes = ("collapse",)


@admin.register(CapitalRepair)
class CapitalRepairAdmin(admin.ModelAdmin):
    list_display = (
        "domik", "tariff_per_sqm",
        "collected_total", "spent_total", "balance_badge", "updated_at",
    )
    search_fields = ("domik__address",)
    autocomplete_fields = ("domik",)
    readonly_fields = ("id", "updated_at", "created_at", "balance_badge")
    ordering = ("domik__address",)
    list_per_page = 50
    inlines = [CapitalRepairWorkInline]

    fieldsets = (
        ("Дом", {"fields": ("id", "domik")}),
        ("Показатели", {
            "fields": (
                "tariff_per_sqm",
                "collected_total", "spent_total", "balance_badge",
            ),
        }),
        ("Даты", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Остаток")
    def balance_badge(self, obj):
        if obj is None or obj.pk is None:
            return "—"
        return badge(f"{obj.balance:,.2f} ₽", "#16a34a")


@admin.register(CapitalRepairWork)
class CapitalRepairWorkAdmin(admin.ModelAdmin):
    list_display = (
        "work_type", "domik_link", "planned_year",
        "status_badge", "cost", "contractor",
    )
    list_filter = ("status", "planned_year", "capital_repair__domik")
    search_fields = ("work_type", "contractor", "capital_repair__domik__address")
    autocomplete_fields = ("capital_repair",)
    ordering = ("planned_year", "work_type")
    list_per_page = 50

    @admin.display(description="Дом", ordering="capital_repair__domik__address")
    def domik_link(self, obj):
        url = reverse("admin:apihandler_domik_change", args=[obj.capital_repair.domik.id])
        return format_html('<a href="{}">{}</a>', url, obj.capital_repair.domik.address)

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        colors = {
            "planned": "#2563eb",
            "in_progress": "#d97706",
            "done": "#16a34a",
        }
        return badge(obj.get_status_display(), colors.get(obj.status, "#64748b"))


admin.site.register(Poll, PollAdmin)
admin.site.register(Vote, VoteAdmin)