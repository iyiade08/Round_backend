from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from communities.models import Community, CommunityMembership

from .models import Connection, ConnectionRequest


class ConnectionsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="ada@example.com",
            password="testpass123",
            full_name="Ada Okafor",
        )
        self.receiver = User.objects.create_user(
            email="nnamdi@example.com",
            password="testpass123",
            full_name="Nnamdi Okafor",
        )
        self.third_user = User.objects.create_user(
            email="chioma@example.com",
            password="testpass123",
            full_name="Chioma Nwosu",
        )

        self.user.profile.family_name = "Okafor"
        self.user.profile.village = "Umuahia"
        self.user.profile.clan = "Aro"
        self.user.profile.save()

        self.receiver.profile.family_name = "Okafor"
        self.receiver.profile.village = "Umuahia"
        self.receiver.profile.clan = "Aro"
        self.receiver.profile.save()

        self.third_user.profile.family_name = "Nwosu"
        self.third_user.profile.village = "Nsukka"
        self.third_user.profile.clan = "Udi"
        self.third_user.profile.save()

        self.community = Community.objects.create(
            name="Okafor Family Circle",
            community_type=Community.CommunityType.FAMILY,
            visibility=Community.Visibility.PUBLIC,
            created_by=self.user,
        )
        CommunityMembership.objects.create(
            user=self.user,
            community=self.community,
            role=CommunityMembership.Role.OWNER,
            status=CommunityMembership.Status.ACTIVE,
        )
        CommunityMembership.objects.create(
            user=self.receiver,
            community=self.community,
            role=CommunityMembership.Role.MEMBER,
            status=CommunityMembership.Status.ACTIVE,
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_people_list_requires_authentication(self):
        response = self.client.get(reverse("connections:people-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_people_list_excludes_current_user_and_supports_search(self):
        self.authenticate()

        response = self.client.get(
            reverse("connections:people-list"),
            {"search": "okafor"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = {person["email"] for person in response.data}
        self.assertEqual(emails, {"nnamdi@example.com"})
        self.assertEqual(response.data[0]["connection_status"], "none")

    def test_recommendations_use_profile_and_shared_community_reasons(self):
        self.authenticate()

        response = self.client.get(reverse("connections:people-recommendations"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["user"]["email"], self.receiver.email)
        self.assertIn("Same family name", response.data[0]["reasons"])
        self.assertIn("Same clan", response.data[0]["reasons"])
        self.assertIn("Same village", response.data[0]["reasons"])
        self.assertIn("Shared community: Okafor Family Circle", response.data[0]["reasons"])

    def test_send_connection_request_creates_pending_request(self):
        self.authenticate()

        response = self.client.post(
            reverse("connections:connection-request-list-create"),
            {
                "receiver_id": str(self.receiver.id),
                "message": "Let us connect.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], ConnectionRequest.Status.PENDING)
        self.assertEqual(response.data["direction"], "sent")
        self.assertTrue(
            ConnectionRequest.objects.filter(
                sender=self.user,
                receiver=self.receiver,
                status=ConnectionRequest.Status.PENDING,
            ).exists()
        )

    def test_duplicate_pending_request_is_rejected(self):
        ConnectionRequest.objects.create(sender=self.user, receiver=self.receiver)
        self.authenticate()

        response = self.client.post(
            reverse("connections:connection-request-list-create"),
            {"receiver_id": str(self.receiver.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_receiver_can_accept_connection_request(self):
        connection_request = ConnectionRequest.objects.create(
            sender=self.user,
            receiver=self.receiver,
        )
        self.authenticate(self.receiver)

        response = self.client.post(
            reverse(
                "connections:connection-request-accept",
                kwargs={"pk": connection_request.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        connection_request.refresh_from_db()
        self.assertEqual(connection_request.status, ConnectionRequest.Status.ACCEPTED)
        self.assertIsNotNone(connection_request.responded_at)
        self.assertEqual(Connection.objects.count(), 1)
        self.assertEqual(response.data["user"]["email"], self.user.email)

    def test_sender_cannot_accept_their_own_connection_request(self):
        connection_request = ConnectionRequest.objects.create(
            sender=self.user,
            receiver=self.receiver,
        )
        self.authenticate(self.user)

        response = self.client.post(
            reverse(
                "connections:connection-request-accept",
                kwargs={"pk": connection_request.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_receiver_can_reject_connection_request(self):
        connection_request = ConnectionRequest.objects.create(
            sender=self.user,
            receiver=self.receiver,
        )
        self.authenticate(self.receiver)

        response = self.client.post(
            reverse(
                "connections:connection-request-reject",
                kwargs={"pk": connection_request.pk},
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        connection_request.refresh_from_db()
        self.assertEqual(connection_request.status, ConnectionRequest.Status.REJECTED)
        self.assertFalse(Connection.objects.exists())

    def test_connection_request_list_can_filter_by_direction_and_status(self):
        ConnectionRequest.objects.create(sender=self.user, receiver=self.receiver)
        ConnectionRequest.objects.create(sender=self.third_user, receiver=self.user)
        self.authenticate()

        response = self.client.get(
            reverse("connections:connection-request-list-create"),
            {
                "direction": "received",
                "status": ConnectionRequest.Status.PENDING,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["sender"]["email"], self.third_user.email)
        self.assertEqual(response.data[0]["direction"], "received")

    def test_list_and_delete_connections(self):
        connection = Connection.objects.create(user_a=self.user, user_b=self.receiver)
        self.authenticate()

        list_response = self.client.get(reverse("connections:connection-list"))

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["user"]["email"], self.receiver.email)

        delete_response = self.client.delete(
            reverse("connections:connection-detail", kwargs={"pk": connection.pk}),
        )

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Connection.objects.exists())
