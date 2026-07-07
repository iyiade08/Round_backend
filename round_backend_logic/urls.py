from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/communities/", include("communities.urls")),
    path("api/v1/community-memberships/", include("communities.membership_urls")),
    path("api/v1/dashboard/", include("dashboard.urls")),
    path("api/v1/", include("connections.urls")),
]
