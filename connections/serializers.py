from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Connection, ConnectionRequest
from .services import get_connection_status


User = get_user_model()


class PersonProfileSerializer(serializers.Serializer):
    location = serializers.CharField()
    family_name = serializers.CharField()
    house = serializers.CharField()
    village = serializers.CharField()
    clan = serializers.CharField()


class PersonSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    connection_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "avatar_initials",
            "phone_number",
            "profile",
            "connection_status",
        )

    def get_profile(self, user):
        profile = getattr(user, "profile", None)
        if not profile:
            return None

        return PersonProfileSerializer(profile).data

    def get_connection_status(self, user):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return "none"

        return get_connection_status(request.user, user)


class ConnectionRequestCreateSerializer(serializers.Serializer):
    receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="receiver",
        write_only=True,
    )
    message = serializers.CharField(required=False, allow_blank=True)


class ConnectionRequestSerializer(serializers.ModelSerializer):
    sender = PersonSerializer(read_only=True)
    receiver = PersonSerializer(read_only=True)
    direction = serializers.SerializerMethodField()

    class Meta:
        model = ConnectionRequest
        fields = (
            "id",
            "sender",
            "receiver",
            "message",
            "status",
            "direction",
            "created_at",
            "updated_at",
            "responded_at",
        )

    def get_direction(self, connection_request):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        if connection_request.sender_id == request.user.id:
            return "sent"
        if connection_request.receiver_id == request.user.id:
            return "received"
        return None


class ConnectionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Connection
        fields = (
            "id",
            "user",
            "connected_at",
            "created_at",
            "updated_at",
        )

    def get_user(self, connection):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        other_user = connection.other_user(request.user)
        if not other_user:
            return None

        return PersonSerializer(other_user, context=self.context).data


class PersonRecommendationSerializer(serializers.Serializer):
    user = PersonSerializer()
    score = serializers.IntegerField()
    reasons = serializers.ListField(child=serializers.CharField())
