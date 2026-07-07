from django.urls import path

from .views import (
    ConnectionDetailView,
    ConnectionRequestAcceptView,
    ConnectionRequestListCreateView,
    ConnectionRequestRejectView,
    ConnectionsListView,
    PeopleListView,
    PeopleRecommendationsView,
)

app_name = "connections"

urlpatterns = [
    path("people/", PeopleListView.as_view(), name="people-list"),
    path("people/recommendations/", PeopleRecommendationsView.as_view(), name="people-recommendations"),
    path("connections/", ConnectionsListView.as_view(), name="connection-list"),
    path("connections/<uuid:pk>/", ConnectionDetailView.as_view(), name="connection-detail"),
    path("connections/requests/", ConnectionRequestListCreateView.as_view(), name="connection-request-list-create"),
    path("connections/requests/<uuid:pk>/accept/", ConnectionRequestAcceptView.as_view(), name="connection-request-accept"),
    path("connections/requests/<uuid:pk>/reject/", ConnectionRequestRejectView.as_view(), name="connection-request-reject"),
]
