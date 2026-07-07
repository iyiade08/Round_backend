from django.urls import path

from .views import MeView, PasswordResetConfirmView, PasswordResetRequestView, SessionView

app_name = "accounts"

urlpatterns = [
    path("session/", SessionView.as_view(), name="session"),
    path("me/", MeView.as_view(), name="me"),
    path("password-reset/request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
