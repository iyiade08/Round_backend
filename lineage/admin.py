from django.contrib import admin

from .models import Ancestor, Clan, FamilyBranch, HistoricalRecord, LineageRecord, Village


@admin.register(Clan)
class ClanAdmin(admin.ModelAdmin):
    list_display = ("name", "origin_location", "created_by", "created_at")
    search_fields = ("name", "description", "origin_location")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ("name", "clan", "location", "created_by", "created_at")
    list_filter = ("clan",)
    search_fields = ("name", "location", "description", "clan__name")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(FamilyBranch)
class FamilyBranchAdmin(admin.ModelAdmin):
    list_display = ("name", "family_name", "clan", "village", "community", "created_by")
    list_filter = ("clan", "village", "community")
    search_fields = ("name", "family_name", "description", "clan__name", "village__name")
    prepopulated_fields = {"slug": ("name",)}


class AncestorInline(admin.TabularInline):
    model = Ancestor
    extra = 0


class HistoricalRecordInline(admin.TabularInline):
    model = HistoricalRecord
    extra = 0


@admin.register(LineageRecord)
class LineageRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "record_type", "visibility", "status", "community", "created_by", "created_at")
    list_filter = ("record_type", "visibility", "status", "community", "clan", "village")
    search_fields = ("title", "summary", "story", "source", "created_by__email", "created_by__full_name")
    filter_horizontal = ("allowed_users", "editor_users")
    inlines = (AncestorInline, HistoricalRecordInline)
