from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from communities.models import Community, CommunityMembership


class DashboardApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpass123",
            full_name="Test User",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            full_name="Other User",
        )

        self.family = Community.objects.create(
            name="Okafor Family Circle",
            community_type=Community.CommunityType.FAMILY,
            description="Extended family network.",
            location="Lagos, Nigeria",
            visibility=Community.Visibility.PUBLIC,
            created_by=self.user,
        )
        self.family_membership = CommunityMembership.objects.create(
            user=self.user,
            community=self.family,
            role=CommunityMembership.Role.OWNER,
            status=CommunityMembership.Status.ACTIVE,
            contribution_total=Decimal("1500.50"),
        )

        self.professional = Community.objects.create(
            name="Builders Network",
            community_type=Community.CommunityType.PROFESSIONAL,
            visibility=Community.Visibility.PUBLIC,
            created_by=self.other_user,
        )
        CommunityMembership.objects.create(
            user=self.user,
            community=self.professional,
            role=CommunityMembership.Role.MEMBER,
            status=CommunityMembership.Status.ACTIVE,
            contribution_total=Decimal("999.50"),
        )

        self.private_clan = Community.objects.create(
            name="Private Clan",
            community_type=Community.CommunityType.CLAN,
            visibility=Community.Visibility.PRIVATE,
            created_by=self.other_user,
        )
        CommunityMembership.objects.create(
            user=self.user,
            community=self.private_clan,
            role=CommunityMembership.Role.MEMBER,
            status=CommunityMembership.Status.REQUESTED,
            contribution_total=Decimal("300.00"),
        )

        self.archived = Community.objects.create(
            name="Archived Community",
            community_type=Community.CommunityType.VILLAGE,
            status=Community.Status.ARCHIVED,
            created_by=self.user,
        )
        CommunityMembership.objects.create(
            user=self.user,
            community=self.archived,
            role=CommunityMembership.Role.MEMBER,
            status=CommunityMembership.Status.ACTIVE,
            contribution_total=Decimal("1000.00"),
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_dashboard_summary_requires_authentication(self):
        response = self.client.get(reverse("dashboard:summary"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_summary_returns_counts_and_contributions(self):
        self.authenticate()

        response = self.client.get(reverse("dashboard:summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], self.user.email)
        self.assertEqual(response.data["stats"]["communities"], 2)
        self.assertEqual(response.data["stats"]["connections"], 0)
        self.assertEqual(response.data["stats"]["events"], 0)
        self.assertEqual(response.data["stats"]["contributions"], "2500.00")
        self.assertEqual(response.data["savings"], {})
        self.assertEqual(response.data["investments"], {})

    def test_dashboard_my_communities_returns_active_communities_only(self):
        self.authenticate()

        response = self.client.get(reverse("dashboard:my-communities"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        community_names = {community["name"] for community in response.data}
        self.assertEqual(community_names, {"Okafor Family Circle", "Builders Network"})
        self.assertEqual(len(response.data), 2)

    def test_dashboard_activity_returns_recent_membership_activity(self):
        self.authenticate()

        response = self.client.get(reverse("dashboard:activity"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        activity_types = {activity["type"] for activity in response.data}
        self.assertIn("community_created", activity_types)
        self.assertIn("community_joined", activity_types)
        self.assertIn("community_join_requested", activity_types)

    def test_dashboard_payment_reminders_returns_empty_list_until_finance_exists(self):
        self.authenticate()

        response = self.client.get(reverse("dashboard:payment-reminders"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_dashboard_life_circle_map_links_user_to_active_communities(self):
        self.authenticate()

        response = self.client.get(reverse("dashboard:life-circle-map"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["center"], str(self.user.id))
        self.assertEqual(len(response.data["nodes"]), 3)
        self.assertEqual(len(response.data["links"]), 2)

        linked_targets = {link["target"] for link in response.data["links"]}
        self.assertEqual(
            linked_targets,
            {str(self.family.id), str(self.professional.id)},
        )
