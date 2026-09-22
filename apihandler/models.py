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


class Domik(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=255)
    fias_id = models.CharField(max_length=100, blank=True)
    management_org = models.CharField(max_length=255, blank=True)
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
        # гарантируем, что у пользователя только одна основная квартира
        if self.is_primary:
            UserApartment.objects.filter(
                user=self.user, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)



class JKDomik(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="jk_domiks")
    domik = models.ForeignKey(Domik, on_delete=models.CASCADE, related_name="jk_users")

    class Meta:
        unique_together = ("user", "domik")
        ordering = ["domik__address"]

    def __str__(self):
        return f"{self.user} @ {self.domik}"