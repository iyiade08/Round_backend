from django.urls import path

from .views import (
    CommunityAnnouncementListCreateView,
    CommunityCommerceListCreateView,
    CommunityForumPostListCreateView,
    CommunityGalleryListCreateView,
    ForumReplyListCreateView,
)

app_name = "feeds"

urlpatterns = [
    path(
        "communities/<uuid:community_id>/announcements/",
        CommunityAnnouncementListCreateView.as_view(),
        name="community-announcements",
    ),
    path(
        "communities/<uuid:community_id>/forum-posts/",
        CommunityForumPostListCreateView.as_view(),
        name="community-forum-posts",
    ),
    path(
        "forum-posts/<uuid:post_id>/replies/",
        ForumReplyListCreateView.as_view(),
        name="forum-post-replies",
    ),
    path(
        "communities/<uuid:community_id>/gallery/",
        CommunityGalleryListCreateView.as_view(),
        name="community-gallery",
    ),
    path(
        "communities/<uuid:community_id>/commerce/",
        CommunityCommerceListCreateView.as_view(),
        name="community-commerce",
    ),
]
