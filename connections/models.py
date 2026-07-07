from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from common.models import TimeStampedModel


class ConnectionRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_connection_requests",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_connection_requests",
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(sender=F("receiver")),
                name="connection_request_sender_receiver_different",
            ),
            models.UniqueConstraint(
                fields=["sender", "receiver"],
                condition=Q(status="pending"),
                name="unique_pending_directed_connection_request",
            ),
        ]
        indexes = [
            models.Index(fields=["sender", "status"]),
            models.Index(fields=["receiver", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def mark_responded(self, status):
        self.status = status
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "responded_at", "updated_at"])

    def __str__(self):
        return f"{self.sender.email} -> {self.receiver.email} ({self.status})"


class Connection(TimeStampedModel):
    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connections_as_user_a",
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connections_as_user_b",
    )
    connected_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-connected_at"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(user_a=F("user_b")),
                name="connection_users_different",
            ),
            models.UniqueConstraint(
                fields=["user_a", "user_b"],
                name="unique_connection_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["user_a", "connected_at"]),
            models.Index(fields=["user_b", "connected_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.user_a_id and self.user_b_id and str(self.user_a_id) > str(self.user_b_id):
            user_a = self._state.fields_cache.get("user_a")
            user_b = self._state.fields_cache.get("user_b")
            self.user_a_id, self.user_b_id = self.user_b_id, self.user_a_id
            if user_a is not None and user_b is not None:
                self.user_a = user_b
                self.user_b = user_a
        super().save(*args, **kwargs)

    def other_user(self, user):
        if self.user_a_id == user.id:
            return self.user_b
        if self.user_b_id == user.id:
            return self.user_a
        return None

    def __str__(self):
        return f"{self.user_a.email} <-> {self.user_b.email}"


class PersonRecommendation(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="person_recommendations",
    )
    recommended_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommended_to_users",
    )
    score = models.PositiveIntegerField(default=0)
    reasons = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-score", "recommended_user__full_name"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(user=F("recommended_user")),
                name="person_recommendation_users_different",
            ),
            models.UniqueConstraint(
                fields=["user", "recommended_user"],
                name="unique_person_recommendation",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "score"]),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.recommended_user.email} ({self.score})"
