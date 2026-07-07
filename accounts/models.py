import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.crypto import salted_hmac
from django.utils import timezone

from common.models import TimeStampedModel


def build_initials(name_or_email):
    source = (name_or_email or "").strip()
    if not source:
        return ""

    if "@" in source:
        source = source.split("@", 1)[0]

    parts = [part for part in source.replace(".", " ").replace("_", " ").split() if part]
    if not parts:
        return source[:2].upper()
    return "".join(part[0] for part in parts[:2]).upper()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        UserProfile.objects.get_or_create(user=user)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("full_name", email)
        extra_fields.setdefault("avatar_initials", build_initials(email))

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=180)
    avatar_initials = models.CharField(max_length=8, blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["full_name", "email"]

    def save(self, *args, **kwargs):
        if not self.avatar_initials:
            self.avatar_initials = build_initials(self.full_name or self.email)
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split(" ", 1)[0] if self.full_name else self.email

    def __str__(self):
        return self.email


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    location = models.CharField(max_length=180, blank=True)
    bio = models.TextField(blank=True)
    family_name = models.CharField(max_length=120, blank=True)
    house = models.CharField(max_length=120, blank=True)
    village = models.CharField(max_length=120, blank=True)
    clan = models.CharField(max_length=120, blank=True)
    join_date = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["user__full_name"]

    def __str__(self):
        return f"{self.user.email} profile"


class PasswordResetCode(TimeStampedModel):
    class CodeType(models.TextChoices):
        NUMERIC = "numeric", "Numeric"
        ALPHANUMERIC = "alphanumeric", "Alphanumeric"

    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=128)
    code_type = models.CharField(
        max_length=32,
        choices=CodeType.choices,
        default=CodeType.NUMERIC,
    )
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "used_at", "expires_at"]),
        ]

    @staticmethod
    def hash_code(email, code):
        return salted_hmac(
            "accounts.PasswordResetCode",
            f"{email.lower()}:{code.upper()}",
        ).hexdigest()

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def can_attempt(self):
        return not self.used_at and not self.is_expired() and self.attempts < self.max_attempts

    def check_code(self, code):
        return self.code_hash == self.hash_code(self.email, code)

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at", "updated_at"])

    def __str__(self):
        return f"{self.email} reset code"
