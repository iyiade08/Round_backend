from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import TimeStampedModel
from communities.models import Community


class Event(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    class Category(models.TextChoices):
        MEETING = "meeting", "Meeting"
        CELEBRATION = "celebration", "Celebration"
        FUNDRAISER = "fundraiser", "Fundraiser"
        RELIGIOUS = "religious", "Religious"
        EDUCATION = "education", "Education"
        SPORTS = "sports", "Sports"
        OTHER = "other", "Other"

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="events",
    )
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=32, choices=Category.choices, default=Category.MEETING)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=80, default="Africa/Lagos")
    location_name = models.CharField(max_length=220, blank=True)
    virtual_url = models.URLField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PUBLISHED)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_events",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["starts_at", "title"]
        indexes = [
            models.Index(fields=["community", "status", "starts_at"]),
            models.Index(fields=["status", "starts_at"]),
            models.Index(fields=["category"]),
            models.Index(fields=["created_by", "starts_at"]),
        ]

    def is_upcoming(self):
        return self.starts_at >= timezone.now()

    def __str__(self):
        return self.title


class EventRSVP(TimeStampedModel):
    class Status(models.TextChoices):
        ATTENDING = "attending", "Attending"
        INTERESTED = "interested", "Interested"
        DECLINED = "declined", "Declined"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="rsvps",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_rsvps",
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ATTENDING)
    note = models.CharField(max_length=240, blank=True)
    responded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-responded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="unique_event_rsvp_per_user",
            ),
        ]
        indexes = [
            models.Index(fields=["event", "status"]),
            models.Index(fields=["user", "responded_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            self.responded_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} RSVP for {self.event.title}"
