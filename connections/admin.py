from django.contrib import admin

from .models import Connection, ConnectionRequest, PersonRecommendation


@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "status", "created_at", "responded_at")
    list_filter = ("status", "created_at", "responded_at")
    search_fields = ("sender__email", "sender__full_name", "receiver__email", "receiver__full_name")


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ("user_a", "user_b", "connected_at")
    list_filter = ("connected_at",)
    search_fields = ("user_a__email", "user_a__full_name", "user_b__email", "user_b__full_name")


@admin.register(PersonRecommendation)
class PersonRecommendationAdmin(admin.ModelAdmin):
    list_display = ("user", "recommended_user", "score", "created_at")
    list_filter = ("score", "created_at")
    search_fields = ("user__email", "user__full_name", "recommended_user__email", "recommended_user__full_name")
