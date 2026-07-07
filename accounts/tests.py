from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import PasswordResetCode, User


class PasswordResetApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="oldpassword123",
            full_name="Test User",
            firebase_uid="firebase-user-id",
        )

    def test_password_reset_request_returns_six_digit_code_for_existing_user(self):
        response = self.client.post(
            reverse("accounts:password-reset-request"),
            {"email": "TEST@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["code_type"], PasswordResetCode.CodeType.NUMERIC)
        self.assertEqual(response.data["code_length"], 6)
        self.assertEqual(len(response.data["reset_code"]), 6)
        self.assertTrue(response.data["reset_code"].isdigit())
        self.assertTrue(
            PasswordResetCode.objects.filter(
                email="test@example.com",
                used_at__isnull=True,
            ).exists()
        )

    def test_password_reset_request_can_return_alphanumeric_code(self):
        response = self.client.post(
            reverse("accounts:password-reset-request"),
            {
                "email": self.user.email,
                "code_type": PasswordResetCode.CodeType.ALPHANUMERIC,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code_type"], PasswordResetCode.CodeType.ALPHANUMERIC)
        self.assertEqual(len(response.data["reset_code"]), 6)
        self.assertTrue(response.data["reset_code"].isalnum())

    def test_password_reset_request_does_not_return_code_for_unknown_email(self):
        response = self.client.post(
            reverse("accounts:password-reset-request"),
            {"email": "missing@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["reset_code"])

    @patch("accounts.services.update_user_password")
    def test_password_reset_confirm_updates_firebase_and_local_password(self, mock_update_password):
        request_response = self.client.post(
            reverse("accounts:password-reset-request"),
            {"email": self.user.email},
            format="json",
        )
        code = request_response.data["reset_code"]

        response = self.client.post(
            reverse("accounts:password-reset-confirm"),
            {
                "email": self.user.email,
                "code": code,
                "new_password": "newpassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_update_password.assert_called_once_with(
            email=self.user.email,
            password="newpassword123",
            firebase_uid=self.user.firebase_uid,
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))
        reset_code = PasswordResetCode.objects.get(email=self.user.email)
        self.assertIsNotNone(reset_code.used_at)

    @patch("accounts.services.update_user_password")
    def test_password_reset_confirm_rejects_invalid_code(self, mock_update_password):
        self.client.post(
            reverse("accounts:password-reset-request"),
            {"email": self.user.email},
            format="json",
        )

        response = self.client.post(
            reverse("accounts:password-reset-confirm"),
            {
                "email": self.user.email,
                "code": "000000",
                "new_password": "newpassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_update_password.assert_not_called()
        reset_code = PasswordResetCode.objects.get(email=self.user.email)
        self.assertEqual(reset_code.attempts, 1)
