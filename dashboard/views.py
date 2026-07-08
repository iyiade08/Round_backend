from decimal import Decimal

from django.db.models import Count, Q, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from communities.models import Community, CommunityMembership
from connections.models import Connection
from events.permissions import visible_events_for_user

from .serializers import (
    DashboardActivitySerializer,
    DashboardCommunitySerializer,
    DashboardSummarySerializer,
    PaymentReminderSerializer,
)


def _format_money(value):
    amount = value or Decimal("0.00")
    return f"{amount.quantize(Decimal('0.01'))}"


def _dashboard_communities_for_user(user):
    return (
        Community.objects.filter(
            memberships__user=user,
            memberships__status=CommunityMembership.Status.ACTIVE,
            status=Community.Status.ACTIVE,
        )
        .select_related("created_by")
        .annotate(
            active_members_count=Count(
                "memberships",
                filter=Q(memberships__status=CommunityMembership.Status.ACTIVE),
                distinct=True,
            )
        )
        .distinct()
        .order_by("name")
    )


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_memberships = CommunityMembership.objects.filter(
            user=request.user,
            status=CommunityMembership.Status.ACTIVE,
            community__status=Community.Status.ACTIVE,
        )
        contribution_total = active_memberships.aggregate(
            total=Sum("contribution_total"),
        )["total"]
        connections_count = Connection.objects.filter(
            Q(user_a=request.user) | Q(user_b=request.user)
        ).count()
        events_count = visible_events_for_user(request.user).count()

        data = {
            "user": request.user,
            "stats": {
                "connections": connections_count,
                "communities": active_memberships.values("community_id").distinct().count(),
                "events": events_count,
                "contributions": _format_money(contribution_total),
            },
            "savings": {},
            "investments": {},
        }
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)


class DashboardActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = (
            CommunityMembership.objects.filter(
                user=request.user,
                community__status=Community.Status.ACTIVE,
            )
            .exclude(
                status__in=[
                    CommunityMembership.Status.LEFT,
                    CommunityMembership.Status.SUSPENDED,
                ],
            )
            .select_related("community", "community__created_by")
            .order_by("-updated_at")[:20]
        )

        activities = []
        for membership in memberships:
            community = membership.community
            if membership.role == CommunityMembership.Role.OWNER:
                activity_type = "community_created"
                title = f"Created {community.name}"
                occurred_at = community.created_at
            elif membership.status == CommunityMembership.Status.REQUESTED:
                activity_type = "community_join_requested"
                title = f"Requested to join {community.name}"
                occurred_at = membership.updated_at
            else:
                activity_type = "community_joined"
                title = f"Joined {community.name}"
                occurred_at = membership.joined_at

            activities.append(
                {
                    "id": str(membership.id),
                    "type": activity_type,
                    "title": title,
                    "description": community.description,
                    "occurred_at": occurred_at,
                    "community": community,
                }
            )

        serializer = DashboardActivitySerializer(
            activities,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class DashboardPaymentRemindersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = PaymentReminderSerializer([], many=True, context={"request": request})
        return Response(serializer.data)


class DashboardMyCommunitiesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        communities = _dashboard_communities_for_user(request.user)
        serializer = DashboardCommunitySerializer(
            communities,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class DashboardLifeCircleMapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        communities = _dashboard_communities_for_user(request.user)
        community_data = DashboardCommunitySerializer(
            communities,
            many=True,
            context={"request": request},
        ).data

        user_node_id = str(request.user.id)
        nodes = [
            {
                "id": user_node_id,
                "type": "user",
                "label": request.user.full_name,
                "avatar_initials": request.user.avatar_initials,
            }
        ]
        links = []

        for community in community_data:
            community_id = str(community["id"])
            membership = community.get("my_membership") or {}
            nodes.append(
                {
                    "id": community_id,
                    "type": community["type"],
                    "label": community["name"],
                    "location": community["location"],
                    "members_count": community["members_count"],
                }
            )
            links.append(
                {
                    "source": user_node_id,
                    "target": community_id,
                    "relationship": membership.get("role", "member"),
                    "status": membership.get("status", "active"),
                }
            )

        return Response(
            {
                "center": user_node_id,
                "nodes": nodes,
                "links": links,
            }
        )
