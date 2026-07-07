from django.urls import path

from .views import (
    DashboardActivityView,
    DashboardLifeCircleMapView,
    DashboardMyCommunitiesView,
    DashboardPaymentRemindersView,
    DashboardSummaryView,
)

app_name = "dashboard"

urlpatterns = [
    path("summary/", DashboardSummaryView.as_view(), name="summary"),
    path("activity/", DashboardActivityView.as_view(), name="activity"),
    path("payment-reminders/", DashboardPaymentRemindersView.as_view(), name="payment-reminders"),
    path("my-communities/", DashboardMyCommunitiesView.as_view(), name="my-communities"),
    path("life-circle-map/", DashboardLifeCircleMapView.as_view(), name="life-circle-map"),
]
