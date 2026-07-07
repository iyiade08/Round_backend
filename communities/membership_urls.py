from django.urls import path

from .views import CommunityMembershipDetailView

app_name = "community_memberships"

urlpatterns = [
    path("<uuid:pk>/", CommunityMembershipDetailView.as_view(), name="membership-detail"),
]
