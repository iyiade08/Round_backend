from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Community, CommunityMembership
from .permissions import can_manage_community, can_view_community, visible_communities_for_user
from .serializers import (
    CommunityMembershipSerializer,
    CommunityMembershipUpdateSerializer,
    CommunitySerializer,
)
from .services import create_community, join_or_request_community


class CommunityListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        communities = visible_communities_for_user(request.user).select_related("created_by")

        community_type = request.query_params.get("type")
        if community_type:
            communities = communities.filter(community_type=community_type)

        search = request.query_params.get("search")
        if search:
            communities = communities.filter(name__icontains=search)

        serializer = CommunitySerializer(
            communities,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = CommunitySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        community = create_community(
            user=request.user,
            community_data=serializer.validated_data,
        )
        return Response(
            CommunitySerializer(community, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MyCommunitiesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        communities = Community.objects.filter(
            memberships__user=request.user,
            memberships__status=CommunityMembership.Status.ACTIVE,
            status=Community.Status.ACTIVE,
        ).select_related("created_by").distinct()
        serializer = CommunitySerializer(
            communities,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class CommunityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        community = get_object_or_404(Community.objects.select_related("created_by"), pk=pk)
        if not can_view_community(request.user, community):
            raise PermissionDenied("You do not have access to this community.")

        return Response(CommunitySerializer(community, context={"request": request}).data)

    def patch(self, request, pk):
        community = get_object_or_404(Community, pk=pk)
        if not can_manage_community(request.user, community):
            raise PermissionDenied("Only community officers can update this community.")

        serializer = CommunitySerializer(
            community,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CommunityMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        community = get_object_or_404(Community, pk=pk)
        if not can_view_community(request.user, community):
            raise PermissionDenied("You do not have access to this community.")

        memberships = community.memberships.filter(
            status=CommunityMembership.Status.ACTIVE,
        ).select_related("user")
        serializer = CommunityMembershipSerializer(memberships, many=True)
        return Response(serializer.data)


class CommunityJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        community = get_object_or_404(Community, pk=pk, status=Community.Status.ACTIVE)
        membership = join_or_request_community(user=request.user, community=community)
        return Response(
            CommunityMembershipSerializer(membership).data,
            status=status.HTTP_200_OK,
        )


class CommunityMembershipDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        membership = get_object_or_404(
            CommunityMembership.objects.select_related("community", "user"),
            pk=pk,
        )
        if not can_manage_community(request.user, membership.community):
            raise PermissionDenied("Only community officers can update memberships.")

        serializer = CommunityMembershipUpdateSerializer(
            membership,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CommunityMembershipSerializer(membership).data)
