from django.contrib import admin

from .models import Announcement, CommunityBusiness, ForumPost, ForumReply, GalleryItem


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "community", "status", "is_pinned", "created_by", "created_at")
    list_filter = ("status", "is_pinned", "community", "created_at")
    search_fields = ("title", "body", "category", "community__name", "created_by__email")


class ForumReplyInline(admin.TabularInline):
    model = ForumReply
    extra = 0


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ("title", "community", "status", "is_pinned", "author", "created_at")
    list_filter = ("status", "is_pinned", "community", "created_at")
    search_fields = ("title", "body", "category", "community__name", "author__email")
    inlines = (ForumReplyInline,)


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ("title", "community", "media_type", "status", "uploader", "created_at")
    list_filter = ("media_type", "status", "community", "created_at")
    search_fields = ("title", "caption", "file_url", "storage_path", "community__name", "uploader__email")


@admin.register(CommunityBusiness)
class CommunityBusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "community", "category", "status", "created_by", "created_at")
    list_filter = ("status", "category", "community", "created_at")
    search_fields = ("name", "description", "category", "community__name", "created_by__email")
