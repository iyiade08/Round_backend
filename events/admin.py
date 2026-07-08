from django.contrib import admin

from .models import Event, EventRSVP


class EventRSVPInline(admin.TabularInline):
    model = EventRSVP
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "community", "category", "status", "starts_at", "created_by")
    list_filter = ("status", "category", "community", "starts_at")
    search_fields = ("title", "description", "location_name", "community__name", "created_by__email")
    inlines = (EventRSVPInline,)


@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ("event", "user", "status", "responded_at")
    list_filter = ("status", "responded_at")
    search_fields = ("event__title", "user__email", "user__full_name")
