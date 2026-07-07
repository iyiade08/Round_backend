import secrets
import string
from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .firebase import update_user_password
from .models import PasswordResetCode, User, UserProfile, build_initials


PROFILE_FIELDS = {
    "location",
    "bio",
    "family_name",
    "house",
    "village",
    "clan",
}

PASSWORD_RESET_CODE_LENGTH = 6
PASSWORD_RESET_CODE_TTL_MINUTES = 10


def _display_name_from_token(decoded_token):
    name = decoded_token.get("name") or ""
    email = decoded_token.get("email") or ""
    return name.strip() or email.split("@", 1)[0]


@transaction.atomic
def sync_firebase_user(decoded_token, profile_data=None):
    profile_data = profile_data or {}
    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")

    if not firebase_uid:
        raise ValueError("Firebase token is missing uid.")
    if not email:
        raise ValueError("Firebase token is missing email.")

    full_name = (
        profile_data.get("full_name")
        or profile_data.get("name")
        or _display_name_from_token(decoded_token)
    )

    user = User.objects.filter(firebase_uid=firebase_uid).first()
    created = False

    if user is None:
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            user = User(email=email)
            created = True
        user.firebase_uid = firebase_uid

    user.email = User.objects.normalize_email(email)
    user.full_name = full_name
    user.avatar_initials = build_initials(full_name or email)

    if "phone_number" in profile_data:
        user.phone_number = profile_data.get("phone_number") or ""

    user.save()

    profile, _ = UserProfile.objects.get_or_create(user=user)
    for field in PROFILE_FIELDS:
        if field in profile_data:
            setattr(profile, field, profile_data.get(field) or "")
    profile.save()

    return user, created


def generate_password_reset_code(code_type=PasswordResetCode.CodeType.NUMERIC):
    if code_type == PasswordResetCode.CodeType.ALPHANUMERIC:
        alphabet = string.ascii_uppercase + string.digits
    else:
        alphabet = string.digits

    return "".join(secrets.choice(alphabet) for _ in range(PASSWORD_RESET_CODE_LENGTH))


@transaction.atomic
def request_password_reset_code(*, email, code_type=PasswordResetCode.CodeType.NUMERIC):
    normalized_email = User.objects.normalize_email(email).lower()
    code = generate_password_reset_code(code_type)
    now = timezone.now()

    PasswordResetCode.objects.filter(
        email__iexact=normalized_email,
        used_at__isnull=True,
    ).update(used_at=now, updated_at=now)

    reset_code = PasswordResetCode.objects.create(
        email=normalized_email,
        code_hash=PasswordResetCode.hash_code(normalized_email, code),
        code_type=code_type,
        expires_at=now + timedelta(minutes=PASSWORD_RESET_CODE_TTL_MINUTES),
    )

    user_exists = User.objects.filter(email__iexact=normalized_email, is_active=True).exists()
    return reset_code, code if user_exists else None


def confirm_password_reset(*, email, code, new_password):
    normalized_email = User.objects.normalize_email(email).lower()
    user = User.objects.filter(email__iexact=normalized_email, is_active=True).first()
    if not user:
        raise ValidationError("Invalid or expired reset code.")

    active_codes = PasswordResetCode.objects.filter(
        email__iexact=normalized_email,
        used_at__isnull=True,
        expires_at__gt=timezone.now(),
        attempts__lt=models.F("max_attempts"),
    ).order_by("-created_at")

    matched_code = None
    for reset_code in active_codes:
        if reset_code.check_code(code):
            matched_code = reset_code
            break

    if not matched_code:
        latest_code = active_codes.first()
        if latest_code:
            latest_code.attempts += 1
            latest_code.save(update_fields=["attempts", "updated_at"])
        raise ValidationError("Invalid or expired reset code.")

    update_user_password(
        email=user.email,
        password=new_password,
        firebase_uid=user.firebase_uid or "",
    )
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    matched_code.mark_used()

    return user
