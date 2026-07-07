from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Community, CommunityMembership


class CommunityApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            full_name="Owner User",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="testpass123",
            full_name="Member User",
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_create_community_creates_owner_membership(self):
        self.authenticate()

        response = self.client.post(
            reverse("communities:community-list-create"),
            {
                "name": "Okafor Family Circle",
                "type": "family",
                "description": "Extended family network.",
                "visibility": "public",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        community = Community.objects.get(name="Okafor Family Circle")
        membership = CommunityMembership.objects.get(user=self.user, community=community)
        self.assertEqual(membership.role, CommunityMembership.Role.OWNER)
        self.assertEqual(membership.status, CommunityMembership.Status.ACTIVE)

    def test_public_community_join_creates_active_membership(self):
        community = Community.objects.create(
            name="Sunrise Neighborhood",
            community_type=Community.CommunityType.NEIGHBORHOOD,
            visibility=Community.Visibility.PUBLIC,
            created_by=self.user,
        )
        self.authenticate(self.member)

        response = self.client.post(
            reverse("communities:community-join", kwargs={"pk": community.pk}),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], CommunityMembership.Status.ACTIVE)

    def test_private_community_join_creates_requested_membership(self):
        community = Community.objects.create(
            name="Private Clan",
            community_type=Community.CommunityType.CLAN,
            visibility=Community.Visibility.PRIVATE,
            created_by=self.user,
        )
        self.authenticate(self.member)

        response = self.client.post(
            reverse("communities:community-join", kwargs={"pk": community.pk}),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], CommunityMembership.Status.REQUESTED)

    def test_non_manager_cannot_update_community(self):
        community = Community.objects.create(
            name="Managed Community",
            community_type=Community.CommunityType.PROFESSIONAL,
            visibility=Community.Visibility.PUBLIC,
            created_by=self.user,
        )
        CommunityMembership.objects.create(
            user=self.member,
            community=community,
            role=CommunityMembership.Role.MEMBER,
            status=CommunityMembership.Status.ACTIVE,
        )
        self.authenticate(self.member)

        response = self.client.patch(
            reverse("communities:community-detail", kwargs={"pk": community.pk}),
            {"name": "Renamed Community"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
