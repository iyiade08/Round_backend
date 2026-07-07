from rest_framework import serializers

from .models import Community, CommunityMembership


class CommunityUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    avatar_initials = serializers.CharField()


class CommunityMembershipSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = CommunityMembership
        fields = (
            "id",
            "user",
            "role",
            "status",
            "joined_at",
            "contribution_total",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "joined_at", "contribution_total", "created_at", "updated_at")

    def get_user(self, membership):
        return CommunityUserSerializer(membership.user).data


class CommunitySerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        source="community_type",
        choices=Community.CommunityType.choices,
    )
    created_by = CommunityUserSerializer(read_only=True)
    members_count = serializers.SerializerMethodField()
    my_membership = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = (
            "id",
            "name",
            "slug",
            "type",
            "description",
            "location",
            "visibility",
            "status",
            "color_key",
            "banner_key",
            "members_count",
            "my_membership",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "status", "members_count", "my_membership", "created_by", "created_at", "updated_at")

    def get_members_count(self, community):
        return community.memberships.filter(status=CommunityMembership.Status.ACTIVE).count()

    def get_my_membership(self, community):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        membership = community.memberships.filter(user=request.user).first()
        if not membership:
            return None

        return {
            "id": membership.id,
            "role": membership.role,
            "status": membership.status,
            "joined_at": membership.joined_at,
        }


class CommunityMembershipUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMembership
        fields = ("role", "status")

    def validate(self, attrs):
        role = attrs.get("role", self.instance.role if self.instance else None)
        status = attrs.get("status")

        if status == CommunityMembership.Status.LEFT and role == CommunityMembership.Role.OWNER:
            raise serializers.ValidationError("An owner cannot be marked as left while still owner.")

        return attrs
