from django.conf import settings
from django.db import models
from django.utils.text import slugify

from common.models import TimeStampedModel
from communities.models import Community


def build_unique_slug(model_class, value, pk=None):
    base_slug = slugify(value)[:180] or "item"
    slug = base_slug
    counter = 2

    while model_class.objects.filter(slug=slug).exclude(pk=pk).exists():
        suffix = f"-{counter}"
        slug = f"{base_slug[:220 - len(suffix)]}{suffix}"
        counter += 1

    return slug


class Clan(TimeStampedModel):
    name = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    origin_location = models.CharField(max_length=180, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_clans",
    )

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self.__class__, self.name, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Village(TimeStampedModel):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    clan = models.ForeignKey(
        Clan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="villages",
    )
    location = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_villages",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "clan"],
                name="unique_village_name_per_clan",
            ),
        ]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self.__class__, self.name, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class FamilyBranch(TimeStampedModel):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    family_name = models.CharField(max_length=120, blank=True)
    clan = models.ForeignKey(
        Clan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="family_branches",
    )
    village = models.ForeignKey(
        Village,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="family_branches",
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="family_branches",
    )
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_family_branches",
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["family_name"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self.__class__, self.name, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class LineageRecord(TimeStampedModel):
    class RecordType(models.TextChoices):
        FAMILY_TREE = "family_tree", "Family tree"
        ORAL_HISTORY = "oral_history", "Oral history"
        MIGRATION = "migration", "Migration"
        BIOGRAPHY = "biography", "Biography"
        ARCHIVE = "archive", "Archive"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        COMMUNITY = "community", "Community"
        PRIVATE = "private", "Private"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=220)
    record_type = models.CharField(
        max_length=32,
        choices=RecordType.choices,
        default=RecordType.FAMILY_TREE,
    )
    summary = models.TextField(blank=True)
    story = models.TextField(blank=True)
    source = models.CharField(max_length=220, blank=True)
    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)
    visibility = models.CharField(
        max_length=32,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    clan = models.ForeignKey(
        Clan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lineage_records",
    )
    village = models.ForeignKey(
        Village,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lineage_records",
    )
    family_branch = models.ForeignKey(
        FamilyBranch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lineage_records",
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lineage_records",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_lineage_records",
    )
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="viewable_lineage_records",
    )
    editor_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="editable_lineage_records",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["record_type"]),
            models.Index(fields=["visibility"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title


class Ancestor(TimeStampedModel):
    class Gender(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        FEMALE = "female", "Female"
        MALE = "male", "Male"

    lineage_record = models.ForeignKey(
        LineageRecord,
        on_delete=models.CASCADE,
        related_name="ancestors",
    )
    full_name = models.CharField(max_length=180)
    gender = models.CharField(max_length=32, choices=Gender.choices, default=Gender.UNKNOWN)
    birth_year = models.IntegerField(null=True, blank=True)
    death_year = models.IntegerField(null=True, blank=True)
    relationship = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "full_name"]

    def __str__(self):
        return self.full_name


class HistoricalRecord(TimeStampedModel):
    lineage_record = models.ForeignKey(
        LineageRecord,
        on_delete=models.CASCADE,
        related_name="historical_records",
    )
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    record_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=220, blank=True)
    file_url = models.URLField(blank=True)
    storage_path = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title
