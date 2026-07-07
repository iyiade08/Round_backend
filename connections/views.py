from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Connection, ConnectionRequest
from .serializers import (
    ConnectionRequestCreateSerializer,
    ConnectionRequestSerializer,
    ConnectionSerializer,
    PersonRecommendationSerializer,
    PersonSerializer,
)
from .services import (
    accept_connection_request,
    delete_connection,
    get_recommendations_for_user,
    reject_connection_request,
    send_connection_request,
)


User = get_user_model()


class PeopleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        people = (
            User.objects.filter(is_active=True)
            .exclude(pk=request.user.pk)
            .select_related("profile")
            .order_by("full_name", "email")
        )

        search = request.query_params.get("search")
        if search:
            people = people.filter(
                Q(full_name__icontains=search)
                | Q(email__icontains=search)
                | Q(profile__family_name__icontains=search)
                | Q(profile__village__icontains=search)
                | Q(profile__clan__icontains=search)
            )

        serializer = PersonSerializer(
            people,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class PeopleRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recommendations = get_recommendations_for_user(request.user)
        serializer = PersonRecommendationSerializer(
            recommendations,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class ConnectionRequestListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        connection_requests = ConnectionRequest.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).select_related("sender", "sender__profile", "receiver", "receiver__profile")

        request_status = request.query_params.get("status")
        if request_status:
            connection_requests = connection_requests.filter(status=request_status)

        direction = request.query_params.get("direction")
        if direction == "sent":
            connection_requests = connection_requests.filter(sender=request.user)
        elif direction == "received":
            connection_requests = connection_requests.filter(receiver=request.user)

        serializer = ConnectionRequestSerializer(
            connection_requests,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = ConnectionRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        connection_request = send_connection_request(
            sender=request.user,
            receiver=serializer.validated_data["receiver"],
            message=serializer.validated_data.get("message", ""),
        )
        return Response(
            ConnectionRequestSerializer(
                connection_request,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class ConnectionRequestAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        connection_request = get_object_or_404(
            ConnectionRequest.objects.select_related("sender", "receiver"),
            pk=pk,
        )
        connection = accept_connection_request(
            user=request.user,
            connection_request=connection_request,
        )
        return Response(
            ConnectionSerializer(connection, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class ConnectionRequestRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        connection_request = get_object_or_404(
            ConnectionRequest.objects.select_related("sender", "receiver"),
            pk=pk,
        )
        connection_request = reject_connection_request(
            user=request.user,
            connection_request=connection_request,
        )
        return Response(
            ConnectionRequestSerializer(
                connection_request,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )


class ConnectionsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        connections = (
            Connection.objects.filter(Q(user_a=request.user) | Q(user_b=request.user))
            .select_related("user_a", "user_a__profile", "user_b", "user_b__profile")
            .order_by("-connected_at")
        )
        serializer = ConnectionSerializer(
            connections,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class ConnectionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        connection = get_object_or_404(Connection, pk=pk)
        delete_connection(user=request.user, connection=connection)
        return Response(status=status.HTTP_204_NO_CONTENT)
