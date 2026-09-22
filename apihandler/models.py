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