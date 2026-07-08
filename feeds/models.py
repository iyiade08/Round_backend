from django.conf import settings
from django.db import models

from common.models import TimeStampedModel
from communities.models import Community


class Announcement(TimeStampedModel):
    class Status(models.TextChoices):
        PUBLISHED = "published", "Published"
        DRAFT = "draft", "Draft"
        ARCHIVED = "archived", "Archived"

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="announcements",
    )
    title = models.CharField(max_length=220)
    body = models.TextField()
    category = models.CharField(max_length=80, blank=True)
    is_pinned = models.BooleanField(default=False)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PUBLISHED)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_announcements",
    )

    class Meta:
        ordering = ["-is_pinned", "-created_at"]
        indexes = [
            models.Index(fields=["community", "status", "created_at"]),
            models.Index(fields=["is_pinned"]),
        ]

    def __str__(self):
        return self.title


class ForumPost(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"
        HIDDEN = "hidden", "Hidden"

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="forum_posts",
    )
    title = models.CharField(max_length=220)
    body = models.TextField()
    category = models.CharField(max_length=80, blank=True)
    is_pinned = models.BooleanField(default=False)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="forum_posts",
    )

    class Meta:
        ordering = ["-is_pinned", "-created_at"]
        indexes = [
            models.Index(fields=["community", "status", "created_at"]),
            models.Index(fields=["author", "created_at"]),
            models.Index(fields=["is_pinned"]),
        ]

    def __str__(self):
        return self.title


class ForumReply(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        HIDDEN = "hidden", "Hidden"

    post = models.ForeignKey(
        ForumPost,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    body = models.TextField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="forum_replies",
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "status", "created_at"]),
            models.Index(fields=["author", "created_at"]),
        ]

    def __str__(self):
        return f"Reply to {self.post.title}"


class GalleryItem(TimeStampedModel):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        DOCUMENT = "document", "Document"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        HIDDEN = "hidden", "Hidden"

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="gallery_items",
    )
    title = models.CharField(max_length=220, blank=True)
    caption = models.TextField(blank=True)
    media_type = models.CharField(max_length=32, choices=MediaType.choices, default=MediaType.IMAGE)
    file_url = models.URLField()
    storage_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    metadata = models.JSONField(default=dict, blank=True)
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="gallery_items",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["community", "status", "created_at"]),
            models.Index(fields=["media_type"]),
        ]

    def __str__(self):
        return self.title or self.caption[:60] or self.file_url


class CommunityBusiness(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PENDING = "pending", "Pending"
        HIDDEN = "hidden", "Hidden"

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="businesses",
    )
    name = models.CharField(max_length=220)
    category = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    address = models.CharField(max_length=240, blank=True)
    logo_url = models.URLField(blank=True)
    storage_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="community_businesses",
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["community", "status", "name"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.name
