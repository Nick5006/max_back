import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, max_id, name, password=None, **extra_fields):
        if not max_id:
            raise ValueError("Нужен max_id")
        if not name:
            raise ValueError("Нужно name")
        user = self.model(max_id=max_id, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, max_id, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_jk", False)

        if not extra_fields["is_staff"]:
            raise ValueError("Суперюзер должен иметь is_staff=True")
        if not extra_fields["is_superuser"]:
            raise ValueError("Суперюзер должен иметь is_superuser=True")

        return self.create_user(max_id, name, password, **extra_fields)

    def create_jkuser(self, max_id, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_jk", True)

        if extra_fields["is_staff"]:
            raise ValueError("ЖкЮзер не должен иметь is_staff=True")
        if extra_fields["is_superuser"]:
            raise ValueError("ЖкЮзер не должен иметь is_superuser=True")
        if not extra_fields["is_jk"]:
            raise ValueError("ЖкЮзер должен иметь is_jk=True")

        return self.create_user(max_id, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    max_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    management_org = models.ForeignKey("ManagementOrganization", on_delete=models.SET_NULL, blank=True, null=True, related_name="jk_users")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_jk = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "max_id"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        ordering = ["-date_joined", "name"]

    def __str__(self):
        return self.max_id

class ManagementOrganization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    inn = models.CharField(max_length=12, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Domik(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=255)
    fias_id = models.CharField(max_length=100, blank=True)
    management_org = models.ForeignKey("ManagementOrganization", on_delete=models.SET_NULL, blank=True, null=True, related_name="domiks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["address"]

    def __str__(self):
        return self.address


class Apartment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domik = models.ForeignKey(Domik, on_delete=models.CASCADE, related_name="apartments")
    number = models.CharField(max_length=20)
    entrance = models.CharField(max_length=10, blank=True)

    class Meta:
        unique_together = ("domik", "number")
        ordering = ["domik__address", "number"]

    def __str__(self):
        return f"{self.domik.address}, кв. {self.number}"


class UserApartment(models.Model):
    class Role(models.TextChoices):
        RESIDENT = "resident", "Житель"
        OWNER = "owner", "Собственник"
        CHAIR = "chair", "Председатель совета МКД"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="user_apartments"
    )
    apartment = models.ForeignKey(
        Apartment, on_delete=models.CASCADE, related_name="user_apartments"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RESIDENT)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "apartment", "role")
        ordering = ["-is_primary", "apartment__domik__address", "apartment__number"]

    def __str__(self):
        return f"{self.user} — {self.apartment} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if self.is_primary:
            UserApartment.objects.filter(
                user=self.user, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class Appeal(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        IN_PROGRESS = "in_progress", "В работе"
        DONE = "done", "Выполнена"
        REJECTED = "rejected", "Отклонена"

    id = models.UUIDField(primary_key = True, default=uuid.uuid4, editable = False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appeals")
    domik = models.ForeignKey(Domik, on_delete=models.CASCADE, related_name="appeals")
    apartment = models.ForeignKey(Apartment, on_delete=models.SET_NULL, related_name="appeals", null = True, blank=True)
    title = models.CharField(max_length = 200)
    description = models.TextField()
    status = models.CharField(max_length = 30, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}"

class AppealHistory(models.Model):
    appeal = models.ForeignKey(Appeal, on_delete=models.CASCADE, related_name="appeal_history")
    status = models.CharField(max_length = 30, choices=Appeal.Status.choices)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField(blank=True)

    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["changed_at"]

class Poll(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="polls")
    domik = models.ForeignKey(Domik, on_delete=models.CASCADE, related_name="polls")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Choice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class Vote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["poll", "user"], name="unique_vote_per_poll"
            )
        ]

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domik = models.ForeignKey(Domik, on_delete=models.CASCADE, related_name="notifications")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="notifications")
    title = models.CharField(max_length = 200)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str(self):
        return self.title

class CapitalRepair(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domik = models.OneToOneField(
        Domik, on_delete=models.CASCADE, related_name="capital_repair"
    )
    tariff_per_sqm = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Руб. за м² в месяц (справочно, устанавливается регионом)",
    )
    collected_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text="Собрано всего, руб. (УК обновляет вручную)",
    )
    spent_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text="Потрачено всего, руб. (УК обновляет вручную)",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def balance(self):
        return self.collected_total - self.spent_total

    def __str__(self):
        return f"Капремонт — {self.domik.address}"


class CapitalRepairWork(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Запланировано"
        IN_PROGRESS = "in_progress", "В работе"
        DONE = "done", "Выполнено"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capital_repair = models.ForeignKey(
        CapitalRepair, on_delete=models.CASCADE, related_name="works"
    )
    work_type = models.CharField(max_length=255)
    planned_year = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNED
    )
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    contractor = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    completed_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["planned_year", "work_type"]

    def __str__(self):
        return f"{self.work_type} ({self.planned_year})"