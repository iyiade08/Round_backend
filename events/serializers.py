from rest_framework import serializers

from communities.models import Community
from communities.permissions import can_view_community

from .models import Event, EventRSVP


class EventUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    avatar_initials = serializers.CharField()


class EventCommunitySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    type = serializers.CharField(source="community_type")
    visibility = serializers.CharField()


class EventRSVPSerializer(serializers.ModelSerializer):
    user = EventUserSerializer(read_only=True)
    event_id = serializers.UUIDField(source="event.id", read_only=True)

    class Meta:
        model = EventRSVP
        fields = (
            "id",
            "event_id",
            "user",
            "status",
            "note",
            "responded_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "event_id", "user", "responded_at", "created_at", "updated_at")


class EventSerializer(serializers.ModelSerializer):
    community = EventCommunitySerializer(read_only=True)
    created_by = EventUserSerializer(read_only=True)
    community_id = serializers.PrimaryKeyRelatedField(
        queryset=Community.objects.all(),
        source="community",
        write_only=True,
    )
    my_rsvp = serializers.SerializerMethodField()
    rsvps_count = serializers.SerializerMethodField()
    attending_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "id",
            "community",
            "community_id",
            "title",
            "description",
            "category",
            "starts_at",
            "ends_at",
            "timezone",
            "location_name",
            "virtual_url",
            "status",
            "created_by",
            "my_rsvp",
            "rsvps_count",
            "attending_count",
            "metadata",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "community",
            "created_by",
            "my_rsvp",
            "rsvps_count",
            "attending_count",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        community = attrs.get("community", getattr(self.instance, "community", None))
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))

        if "community" in attrs and community and request and not can_view_community(request.user, community):
            raise serializers.ValidationError("You do not have access to this community.")

        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError("Event end time must be after start time.")

        if not attrs.get("location_name", getattr(self.instance, "location_name", "")) and not attrs.get(
            "virtual_url",
            getattr(self.instance, "virtual_url", ""),
        ):
            raise serializers.ValidationError("Provide either a location name or a virtual URL.")

        return attrs

    def get_my_rsvp(self, event):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        rsvp = event.rsvps.filter(user=request.user).first()
        if not rsvp:
            return None

        return EventRSVPSerializer(rsvp).data

    def get_rsvps_count(self, event):
        annotated_count = getattr(event, "rsvps_count", None)
        if annotated_count is not None:
            return annotated_count

        return event.rsvps.count()

    def get_attending_count(self, event):
        annotated_count = getattr(event, "attending_count", None)
        if annotated_count is not None:
            return annotated_count

        return event.rsvps.filter(status=EventRSVP.Status.ATTENDING).count()
