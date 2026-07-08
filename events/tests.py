from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from communities.models import Community, CommunityMembership

from .models import Event, EventRSVP


class EventApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            full_name="Owner User",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="testpass123",
            full_name="Member User",
        )
        self.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="testpass123",
            full_name="Outsider User",
        )

        self.community = Community.objects.create(
            name="Okafor Family Circle",
            community_type=Community.CommunityType.FAMILY,
            visibility=Community.Visibility.PRIVATE,
            created_by=self.owner,
        )
        CommunityMembership.objects.create(
            user=self.owner,
            community=self.community,
            role=CommunityMembership.Role.OWNER,
            status=CommunityMembership.Status.ACTIVE,
        )
        CommunityMembership.objects.create(
            user=self.member,
            community=self.community,
            role=CommunityMembership.Role.MEMBER,
            status=CommunityMembership.Status.ACTIVE,
        )

        self.public_community = Community.objects.create(
            name="Public Neighborhood",
            community_type=Community.CommunityType.NEIGHBORHOOD,
            visibility=Community.Visibility.PUBLIC,
            created_by=self.owner,
        )
        CommunityMembership.objects.create(
            user=self.owner,
            community=self.public_community,
            role=CommunityMembership.Role.OWNER,
            status=CommunityMembership.Status.ACTIVE,
        )

        self.starts_at = timezone.now() + timedelta(days=7)
        self.ends_at = self.starts_at + timedelta(hours=2)

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.owner)

    def create_event(self, **overrides):
        data = {
            "community": self.community,
            "title": "Family reunion",
            "description": "Annual family reunion.",
            "category": Event.Category.CELEBRATION,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "timezone": "Africa/Lagos",
            "location_name": "Lagos Hall",
            "status": Event.Status.PUBLISHED,
            "created_by": self.owner,
        }
        data.update(overrides)
        return Event.objects.create(**data)

    def test_event_list_requires_authentication(self):
        response = self.client.get(reverse("events:event-list-create"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_only_community_officers_can_create_events(self):
        payload = {
            "community_id": str(self.community.id),
            "title": "Family reunion",
            "description": "Annual family reunion.",
            "category": Event.Category.CELEBRATION,
            "starts_at": self.starts_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "timezone": "Africa/Lagos",
            "location_name": "Lagos Hall",
            "status": Event.Status.PUBLISHED,
        }

        self.authenticate(self.member)
        member_response = self.client.post(
            reverse("events:event-list-create"),
            payload,
            format="json",
        )

        self.authenticate(self.owner)
        owner_response = self.client.post(
            reverse("events:event-list-create"),
            payload,
            format="json",
        )

        self.assertEqual(member_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(owner_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(owner_response.data["title"], "Family reunion")
        self.assertEqual(Event.objects.count(), 1)

    def test_public_published_events_are_visible_to_authenticated_users(self):
        event = self.create_event(community=self.public_community)
        self.authenticate(self.outsider)

        list_response = self.client.get(reverse("events:event-list-create"))
        detail_response = self.client.get(reverse("events:event-detail", kwargs={"pk": event.pk}))

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

    def test_private_events_are_visible_to_active_members_only(self):
        event = self.create_event()

        self.authenticate(self.outsider)
        outsider_response = self.client.get(reverse("events:event-list-create"))
        outsider_detail = self.client.get(reverse("events:event-detail", kwargs={"pk": event.pk}))

        self.authenticate(self.member)
        member_response = self.client.get(reverse("events:event-list-create"))

        self.assertEqual(outsider_response.status_code, status.HTTP_200_OK)
        self.assertEqual(outsider_response.data, [])
        self.assertEqual(outsider_detail.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(member_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(member_response.data), 1)

    def test_creator_or_officer_can_patch_event_but_member_cannot(self):
        event = self.create_event()

        self.authenticate(self.member)
        member_response = self.client.patch(
            reverse("events:event-detail", kwargs={"pk": event.pk}),
            {"title": "Member edit"},
            format="json",
        )

        self.authenticate(self.owner)
        owner_response = self.client.patch(
            reverse("events:event-detail", kwargs={"pk": event.pk}),
            {"title": "Updated reunion"},
            format="json",
        )

        self.assertEqual(member_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertEqual(owner_response.data["title"], "Updated reunion")

    def test_member_can_rsvp_update_and_delete_rsvp(self):
        event = self.create_event()
        self.authenticate(self.member)

        create_response = self.client.post(
            reverse("events:event-rsvp", kwargs={"pk": event.pk}),
            {
                "status": EventRSVP.Status.ATTENDING,
                "note": "I will come with two relatives.",
            },
            format="json",
        )
        update_response = self.client.post(
            reverse("events:event-rsvp", kwargs={"pk": event.pk}),
            {"status": EventRSVP.Status.INTERESTED},
            format="json",
        )
        detail_response = self.client.get(reverse("events:event-detail", kwargs={"pk": event.pk}))

        self.assertEqual(create_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(EventRSVP.objects.count(), 1)
        self.assertEqual(update_response.data["status"], EventRSVP.Status.INTERESTED)
        self.assertEqual(detail_response.data["my_rsvp"]["status"], EventRSVP.Status.INTERESTED)

        delete_response = self.client.delete(reverse("events:event-rsvp", kwargs={"pk": event.pk}))

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EventRSVP.objects.exists())

    def test_user_cannot_rsvp_to_draft_event(self):
        event = self.create_event(status=Event.Status.DRAFT)
        self.authenticate(self.member)

        response = self.client.post(
            reverse("events:event-rsvp", kwargs={"pk": event.pk}),
            {"status": EventRSVP.Status.ATTENDING},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_community_events_endpoint_returns_events_for_one_community(self):
        self.create_event(title="Private family event")
        self.create_event(
            community=self.public_community,
            title="Public event",
        )
        self.authenticate(self.member)

        response = self.client.get(
            reverse("events:community-events", kwargs={"community_id": self.community.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Private family event")

    def test_dashboard_summary_counts_visible_events(self):
        self.create_event()
        self.authenticate(self.member)

        response = self.client.get(reverse("dashboard:summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stats"]["events"], 1)
