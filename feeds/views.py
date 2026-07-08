from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from communities.models import Community

from .models import Announcement, CommunityBusiness, ForumPost, ForumReply, GalleryItem
from .permissions import can_create_announcement, can_create_member_content, can_view_community_content
from .serializers import (
    AnnouncementSerializer,
    CommunityBusinessSerializer,
    ForumPostSerializer,
    ForumReplySerializer,
    GalleryItemSerializer,
)


def get_visible_community_or_403(user, community_id):
    community = get_object_or_404(Community, pk=community_id, status=Community.Status.ACTIVE)
    if not can_view_community_content(user, community):
        raise PermissionDenied("You do not have access to this community.")
    return community


def require_member_content_permission(user, community):
    if not can_create_member_content(user, community):
        raise PermissionDenied("You must be an active community member to create this content.")


class CommunityAnnouncementListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, community_id):
        community = get_visible_community_or_403(request.user, community_id)
        announcements = community.announcements.filter(
            status=Announcement.Status.PUBLISHED,
        ).select_related("community", "created_by")

        category = request.query_params.get("category")
        if category:
            announcements = announcements.filter(category__iexact=category)

        search = request.query_params.get("search")
        if search:
            announcements = announcements.filter(
                Q(title__icontains=search) | Q(body__icontains=search)
            )

        serializer = AnnouncementSerializer(announcements, many=True)
        return Response(serializer.data)

    def post(self, request, community_id):
        community = get_visible_community_or_403(request.user, community_id)
        if not can_create_announcement(request.user, community):
            raise PermissionDenied("Only community officers can create announcements.")

        serializer = AnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save(community=community, created_by=request.user)
        return Response(
            AnnouncementSerializer(announcement).data,
            status=status.HTTP_201_CREATED,
        )


class CommunityForumPostListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, community_id):
        community = get_visible_community_or_403(request.user, community_id)
        posts = (
            community.forum_posts.filter(status=ForumPost.Status.ACTIVE)
            .select_related("community", "author")
            .annotate(
                active_replies_count=Count(
                    "replies",
                    filter=Q(replies__status=ForumReply.Status.ACTIVE),
                )
            )
        )

        category = request.query_params.get("category")
        if category:
            posts = posts.filter(category__iexact=category)

        search = request.query_params.get("search")
        if search:
            posts = posts.filter(
                Q(title__icontains=search) | Q(body__icontains=search)
            )

        serializer = ForumPostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request, community_id):
        community = get_visible_community_or_403(request.user, community_id)
        require_member_content_permission(request.user, community)

        serializer = ForumPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        forum_post = serializer.save(community=community, author=request.user)
        return Response(
            ForumPostSerializer(forum_post).data,
            status=status.HTTP_201_CREATED,
        )


class ForumReplyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        forum_post = get_object_or_404(
            ForumPost.objects.select_related("community", "author"),
            pk=post_id,
            status=ForumPost.Status.ACTIVE,
        )
        if not can_view_community_content(request.user, forum_post.community):
            raise PermissionDenied("You do not have access to this forum post.")

        replies = forum_post.replies.filter(
            status=ForumReply.Status.ACTIVE,
        ).select_related("author")
        serializer = ForumReplySerializer(replies, many=True)
        return Response(serializer.data)

    def post(self, request, post_id):
        forum_post = get_object_or_404(
            ForumPost.objects.select_related("community", "author"),
            pk=post_id,
        )
        if not can_view_community_content(request.user, forum_post.community):
            raise PermissionDenied("You do not have access to this forum post.")
        require_member_content_permission(request.user, forum_post.community)

        if forum_post.status == ForumPost.Status.CLOSED:
            raise ValidationError("This forum post is closed.")
        if forum_post.status == ForumPost.Status.HIDDEN:
            raise PermissionDenied("You do not have access to this forum post.")

        serializer = ForumReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply = serializer.save(post=forum_post, author=request.user)
        return Response(
            ForumReplySerializer(reply).data,
            status=status.HTTP_201_CREATED,
        )


class CommunityGalleryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, community_id):
        community = get_visible_community_or_403(request.user, community_id)
        gallery_items = community.gallery_items.filter(
            status=GalleryItem.Status.ACTIVE,
        ).select_related("community", "uploader")

        media_type = request.query_params.get("media_type")
        if media_type:
            gallery_items = gallery_items.filter(media_type=media_type)

        search = request.query_params.get("search")
        if search:
            gallery_items = gallery_items.filter(
                Q(title__icontains=search) | Q(caption__icontains=search)
            )

        serializer = GalleryItemSerializer(gallery_items, many=True)
        return Response(serializer.data)

    def post(self, request, community_id):
        community = get_visible_community_or_403(request.user, community_id)
        require_member_content_permission(request.user, community)

        serializer = GalleryItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gallery_item = serializer.save(community=community, uploader=request.user)
        return Response(
            GalleryItemSerializer(gallery_item).data,
            status=status.HTTP_201_CREATED,
        )


class CommunityCommerceListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, community_id):
        community = get_visible_community_or_403(request.user, community_id)
        businesses = community.businesses.filter(
            status=CommunityBusiness.Status.ACTIVE,
        ).select_related("community", "created_by")

        category = request.query_params.get("category")
        if category:
            businesses = businesses.filter(category__iexact=category)

        search = request.query_params.get("search")
        if search:
            businesses = businesses.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
            )

        serializer = CommunityBusinessSerializer(businesses, many=True)
        return Response(serializer.data)

    def post(self, request, community_id):
        community = get_visible_community_or_403(request.user, community_id)
        require_member_content_permission(request.user, community)

        serializer = CommunityBusinessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        business = serializer.save(community=community, created_by=request.user)
        return Response(
            CommunityBusinessSerializer(business).data,
            status=status.HTTP_201_CREATED,
        )
