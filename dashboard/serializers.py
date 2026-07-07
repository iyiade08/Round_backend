from rest_framework import serializers

from accounts.serializers import UserSerializer
from communities.models import Community, CommunityMembership


def format_money(value):
    return f"{value:.2f}"


class DashboardCommunitySerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="community_type")
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
            "color_key",
            "banner_key",
            "members_count",
            "my_membership",
        )

    def get_members_count(self, community):
        annotated_count = getattr(community, "active_members_count", None)
        if annotated_count is not None:
            return annotated_count

        return community.memberships.filter(
            status=CommunityMembership.Status.ACTIVE,
        ).count()

    def get_my_membership(self, community):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        membership = community.memberships.filter(user=request.user).first()
        if not membership:
            return None

        return {
            "id": str(membership.id),
            "role": membership.role,
            "status": membership.status,
            "joined_at": membership.joined_at,
            "contribution_total": format_money(membership.contribution_total),
        }


class DashboardSummarySerializer(serializers.Serializer):
    user = UserSerializer()
    stats = serializers.DictField()
    savings = serializers.DictField()
    investments = serializers.DictField()


class DashboardActivitySerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    occurred_at = serializers.DateTimeField()
    community = DashboardCommunitySerializer()


class PaymentReminderSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    due_date = serializers.DateField(allow_null=True)
    status = serializers.CharField()
    community = DashboardCommunitySerializer(allow_null=True)
