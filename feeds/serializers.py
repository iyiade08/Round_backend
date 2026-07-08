from rest_framework import serializers

from .models import Announcement, CommunityBusiness, ForumPost, ForumReply, GalleryItem


class FeedUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    avatar_initials = serializers.CharField()


class FeedCommunitySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    type = serializers.CharField(source="community_type")


class AnnouncementSerializer(serializers.ModelSerializer):
    community = FeedCommunitySerializer(read_only=True)
    created_by = FeedUserSerializer(read_only=True)

    class Meta:
        model = Announcement
        fields = (
            "id",
            "community",
            "title",
            "body",
            "category",
            "is_pinned",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "community", "created_by", "created_at", "updated_at")


class ForumPostSerializer(serializers.ModelSerializer):
    community = FeedCommunitySerializer(read_only=True)
    author = FeedUserSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = ForumPost
        fields = (
            "id",
            "community",
            "title",
            "body",
            "category",
            "is_pinned",
            "status",
            "author",
            "replies_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "community", "author", "status", "replies_count", "created_at", "updated_at")

    def get_replies_count(self, post):
        annotated_count = getattr(post, "active_replies_count", None)
        if annotated_count is not None:
            return annotated_count

        return post.replies.filter(status=ForumReply.Status.ACTIVE).count()


class ForumReplySerializer(serializers.ModelSerializer):
    author = FeedUserSerializer(read_only=True)
    post_id = serializers.UUIDField(source="post.id", read_only=True)

    class Meta:
        model = ForumReply
        fields = (
            "id",
            "post_id",
            "body",
            "status",
            "author",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "post_id", "status", "author", "created_at", "updated_at")


class GalleryItemSerializer(serializers.ModelSerializer):
    community = FeedCommunitySerializer(read_only=True)
    uploader = FeedUserSerializer(read_only=True)

    class Meta:
        model = GalleryItem
        fields = (
            "id",
            "community",
            "title",
            "caption",
            "media_type",
            "file_url",
            "storage_path",
            "status",
            "metadata",
            "uploader",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "community", "status", "uploader", "created_at", "updated_at")


class CommunityBusinessSerializer(serializers.ModelSerializer):
    community = FeedCommunitySerializer(read_only=True)
    created_by = FeedUserSerializer(read_only=True)

    class Meta:
        model = CommunityBusiness
        fields = (
            "id",
            "community",
            "name",
            "category",
            "description",
            "phone_number",
            "email",
            "website",
            "address",
            "logo_url",
            "storage_path",
            "status",
            "metadata",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "community", "status", "created_by", "created_at", "updated_at")
