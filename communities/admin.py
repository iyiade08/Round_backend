from django.contrib import admin

from .models import Community, CommunityMembership


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "community_type", "visibility", "status", "created_by", "created_at")
    list_filter = ("community_type", "visibility", "status")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description", "location", "created_by__email")


@admin.register(CommunityMembership)
class CommunityMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "community", "role", "status", "joined_at")
    list_filter = ("role", "status")
    search_fields = ("user__email", "user__full_name", "community__name")
