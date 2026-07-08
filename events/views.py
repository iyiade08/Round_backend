from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from communities.models import Community
from communities.permissions import can_view_community

from .models import Event, EventRSVP
from .permissions import can_create_event, can_rsvp_event, can_update_event, can_view_event, visible_events_for_user
from .serializers import EventRSVPSerializer, EventSerializer


def event_queryset():
    return (
        Event.objects.select_related("community", "created_by")
        .prefetch_related("rsvps", "rsvps__user")
        .annotate(
            rsvps_count=Count("rsvps", distinct=True),
            attending_count=Count(
                "rsvps",
                filter=Q(rsvps__status=EventRSVP.Status.ATTENDING),
                distinct=True,
            ),
        )
    )


def apply_event_filters(queryset, request):
    category = request.query_params.get("category")
    if category:
        queryset = queryset.filter(category=category)

    event_status = request.query_params.get("status")
    if event_status:
        queryset = queryset.filter(status=event_status)

    community_id = request.query_params.get("community_id")
    if community_id:
        queryset = queryset.filter(community_id=community_id)

    starts_after = request.query_params.get("starts_after")
    if starts_after:
        queryset = queryset.filter(starts_at__gte=starts_after)

    starts_before = request.query_params.get("starts_before")
    if starts_before:
        queryset = queryset.filter(starts_at__lte=starts_before)

    search = request.query_params.get("search")
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(location_name__icontains=search)
        )

    return queryset


class EventListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        visible_events = visible_events_for_user(request.user)
        events = event_queryset().filter(pk__in=visible_events.values("pk"))
        events = apply_event_filters(events, request)

        serializer = EventSerializer(
            events,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = EventSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        community = serializer.validated_data["community"]
        if not can_create_event(request.user, community):
            raise PermissionDenied("Only community officers can create official community events.")

        event = serializer.save(created_by=request.user)
        return Response(
            EventSerializer(event, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class EventDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        event = get_object_or_404(event_queryset(), pk=pk)
        if not can_view_event(request.user, event):
            raise PermissionDenied("You do not have access to this event.")

        serializer = EventSerializer(event, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, pk):
        event = get_object_or_404(event_queryset(), pk=pk)
        if not can_update_event(request.user, event):
            raise PermissionDenied("Only the creator or community officers can update this event.")

        serializer = EventSerializer(
            event,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return Response(EventSerializer(event, context={"request": request}).data)


class EventRSVPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        event = get_object_or_404(Event.objects.select_related("community", "created_by"), pk=pk)
        if not can_rsvp_event(request.user, event):
            raise PermissionDenied("You cannot RSVP to this event.")

        serializer = EventRSVPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rsvp, _ = EventRSVP.objects.update_or_create(
            event=event,
            user=request.user,
            defaults={
                "status": serializer.validated_data.get("status", EventRSVP.Status.ATTENDING),
                "note": serializer.validated_data.get("note", ""),
            },
        )
        return Response(
            EventRSVPSerializer(rsvp).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        event = get_object_or_404(Event.objects.select_related("community", "created_by"), pk=pk)
        rsvp = EventRSVP.objects.filter(event=event, user=request.user).first()
        if not rsvp:
            raise ValidationError("You do not have an RSVP for this event.")

        rsvp.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityEventListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, community_id):
        community = get_object_or_404(Community, pk=community_id, status=Community.Status.ACTIVE)
        if not can_view_community(request.user, community):
            raise PermissionDenied("You do not have access to this community.")

        visible_events = visible_events_for_user(request.user)
        events = event_queryset().filter(
            pk__in=visible_events.values("pk"),
            community=community,
        )
        events = apply_event_filters(events, request)

        serializer = EventSerializer(
            events,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)
