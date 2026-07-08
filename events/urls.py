from django.urls import path

from .views import CommunityEventListView, EventDetailView, EventListCreateView, EventRSVPView

app_name = "events"

urlpatterns = [
    path("events/", EventListCreateView.as_view(), name="event-list-create"),
    path("events/<uuid:pk>/", EventDetailView.as_view(), name="event-detail"),
    path("events/<uuid:pk>/rsvp/", EventRSVPView.as_view(), name="event-rsvp"),
    path("communities/<uuid:community_id>/events/", CommunityEventListView.as_view(), name="community-events"),
]
