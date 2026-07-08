from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Clan, FamilyBranch, LineageRecord, Village
from .permissions import can_edit_lineage_record, can_view_lineage_record, visible_lineage_records_for_user
from .serializers import (
    ClanSerializer,
    FamilyBranchSerializer,
    LineageRecordSerializer,
    VillageSerializer,
)


def lineage_record_queryset():
    return (
        LineageRecord.objects.select_related(
            "clan",
            "village",
            "village__clan",
            "family_branch",
            "family_branch__clan",
            "family_branch__village",
            "family_branch__community",
            "community",
            "created_by",
        )
        .prefetch_related(
            "allowed_users",
            "editor_users",
            "ancestors",
            "historical_records",
        )
    )


class ClanListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clans = Clan.objects.select_related("created_by").order_by("name")
        search = request.query_params.get("search")
        if search:
            clans = clans.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(origin_location__icontains=search)
            )

        serializer = ClanSerializer(clans, many=True)
        return Response(serializer.data)


class VillageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        villages = Village.objects.select_related("clan", "created_by").order_by("name")

        clan_id = request.query_params.get("clan_id")
        if clan_id:
            villages = villages.filter(clan_id=clan_id)

        search = request.query_params.get("search")
        if search:
            villages = villages.filter(
                Q(name__icontains=search)
                | Q(location__icontains=search)
                | Q(description__icontains=search)
            )

        serializer = VillageSerializer(villages, many=True)
        return Response(serializer.data)


class FamilyBranchListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        family_branches = FamilyBranch.objects.select_related(
            "clan",
            "village",
            "village__clan",
            "community",
            "created_by",
        ).order_by("name")

        clan_id = request.query_params.get("clan_id")
        if clan_id:
            family_branches = family_branches.filter(clan_id=clan_id)

        village_id = request.query_params.get("village_id")
        if village_id:
            family_branches = family_branches.filter(village_id=village_id)

        community_id = request.query_params.get("community_id")
        if community_id:
            family_branches = family_branches.filter(community_id=community_id)

        search = request.query_params.get("search")
        if search:
            family_branches = family_branches.filter(
                Q(name__icontains=search)
                | Q(family_name__icontains=search)
                | Q(description__icontains=search)
            )

        serializer = FamilyBranchSerializer(family_branches, many=True)
        return Response(serializer.data)


class LineageRecordListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = visible_lineage_records_for_user(request.user)
        records = lineage_record_queryset().filter(pk__in=records.values("pk"))

        record_type = request.query_params.get("type")
        if record_type:
            records = records.filter(record_type=record_type)

        visibility = request.query_params.get("visibility")
        if visibility:
            records = records.filter(visibility=visibility)

        clan_id = request.query_params.get("clan_id")
        if clan_id:
            records = records.filter(clan_id=clan_id)

        village_id = request.query_params.get("village_id")
        if village_id:
            records = records.filter(village_id=village_id)

        family_branch_id = request.query_params.get("family_branch_id")
        if family_branch_id:
            records = records.filter(family_branch_id=family_branch_id)

        community_id = request.query_params.get("community_id")
        if community_id:
            records = records.filter(community_id=community_id)

        search = request.query_params.get("search")
        if search:
            records = records.filter(
                Q(title__icontains=search)
                | Q(summary__icontains=search)
                | Q(story__icontains=search)
                | Q(source__icontains=search)
            )

        serializer = LineageRecordSerializer(
            records,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = LineageRecordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        lineage_record = serializer.save(created_by=request.user)
        return Response(
            LineageRecordSerializer(
                lineage_record,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class LineageRecordDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        lineage_record = get_object_or_404(lineage_record_queryset(), pk=pk)
        if not can_view_lineage_record(request.user, lineage_record):
            raise PermissionDenied("You do not have access to this lineage record.")

        serializer = LineageRecordSerializer(
            lineage_record,
            context={"request": request},
        )
        return Response(serializer.data)

    def patch(self, request, pk):
        lineage_record = get_object_or_404(lineage_record_queryset(), pk=pk)
        if not can_edit_lineage_record(request.user, lineage_record):
            raise PermissionDenied("Only the owner, editor, or community officers can update this lineage record.")

        serializer = LineageRecordSerializer(
            lineage_record,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        lineage_record = serializer.save()
        return Response(
            LineageRecordSerializer(
                lineage_record,
                context={"request": request},
            ).data
        )
