from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, id, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(id=id, email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, id, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if not extra_fields["is_staff"]:
            raise ValueError("Суперюзер должен иметь is_staff=True")
        if not extra_fields["is_superuser"]:
            raise ValueError("Суперюзер должен иметь is_superuser=True")
        return self.create_user(id, email, name, password, **extra_fields)

    def create_staffuser(self, id, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        if not extra_fields["is_staff"]:
            raise ValueError("Стафюзер должен иметь is_staff=True")
        if extra_fields["is_superuser"]:
            raise ValueError("Стафюзер не должен иметь is_superuser=True")
        return self.create_user(id, email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        ordering = ["-date_joined", "name"]

    def __str__(self):
        return self.email


class Domik(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
