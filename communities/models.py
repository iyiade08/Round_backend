from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from common.models import TimeStampedModel


class Community(TimeStampedModel):
    class CommunityType(models.TextChoices):
        CHURCH = "church", "Church"
        MOSQUE = "mosque", "Mosque"
        NEIGHBORHOOD = "neighborhood", "Neighborhood"
        SCHOOL = "school", "School"
        FAMILY = "family", "Family"
        PROFESSIONAL = "professional", "Professional"
        VILLAGE = "village", "Village"
        CLAN = "clan", "Clan"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"
        INVITE_ONLY = "invite_only", "Invite only"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    community_type = models.CharField(
        max_length=32,
        choices=CommunityType.choices,
        default=CommunityType.FAMILY,
    )
    description = models.TextField(blank=True)
    location = models.CharField(max_length=180, blank=True)
    visibility = models.CharField(
        max_length=32,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_communities",
    )
    color_key = models.CharField(max_length=60, blank=True)
    banner_key = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["community_type"]),
            models.Index(fields=["visibility"]),
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._build_unique_slug()
        super().save(*args, **kwargs)

    def _build_unique_slug(self):
        base_slug = slugify(self.name)[:180] or "community"
        slug = base_slug
        counter = 2

        while Community.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            suffix = f"-{counter}"
            slug = f"{base_slug[:220 - len(suffix)]}{suffix}"
            counter += 1

        return slug

    def __str__(self):
        return self.name


class CommunityMembership(TimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        PRESIDENT = "president", "President"
        SECRETARY = "secretary", "Secretary"
        TREASURER = "treasurer", "Treasurer"
        OFFICER = "officer", "Officer"
        MEMBER = "member", "Member"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INVITED = "invited", "Invited"
        REQUESTED = "requested", "Requested"
        SUSPENDED = "suspended", "Suspended"
        LEFT = "left", "Left"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_memberships",
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    joined_at = models.DateTimeField(default=timezone.now)
    contribution_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        ordering = ["community__name", "user__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "community"],
                name="unique_user_community_membership",
            ),
        ]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["status"]),
            models.Index(fields=["joined_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} in {self.community.name}"
