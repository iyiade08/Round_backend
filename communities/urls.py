from django.urls import path

from .views import (
    CommunityDetailView,
    CommunityJoinView,
    CommunityListCreateView,
    CommunityMembersView,
    MyCommunitiesView,
)

app_name = "communities"

urlpatterns = [
    path("", CommunityListCreateView.as_view(), name="community-list-create"),
    path("my/", MyCommunitiesView.as_view(), name="my-communities"),
    path("<uuid:pk>/", CommunityDetailView.as_view(), name="community-detail"),
    path("<uuid:pk>/members/", CommunityMembersView.as_view(), name="community-members"),
    path("<uuid:pk>/join/", CommunityJoinView.as_view(), name="community-join"),
]
