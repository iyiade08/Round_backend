from django.urls import path

from .views import (
    ClanListView,
    FamilyBranchListView,
    LineageRecordDetailView,
    LineageRecordListCreateView,
    VillageListView,
)

app_name = "lineage"

urlpatterns = [
    path("clans/", ClanListView.as_view(), name="clan-list"),
    path("villages/", VillageListView.as_view(), name="village-list"),
    path("family-branches/", FamilyBranchListView.as_view(), name="family-branch-list"),
    path("records/", LineageRecordListCreateView.as_view(), name="record-list-create"),
    path("records/<uuid:pk>/", LineageRecordDetailView.as_view(), name="record-detail"),
]
