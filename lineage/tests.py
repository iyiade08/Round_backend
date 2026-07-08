from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from communities.models import Community, CommunityMembership

from .models import Ancestor, Clan, FamilyBranch, HistoricalRecord, LineageRecord, Village


class LineageApiTests(APITestCase):
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
        self.editor = User.objects.create_user(
            email="editor@example.com",
            password="testpass123",
            full_name="Editor User",
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

        self.clan = Clan.objects.create(
            name="Aro Clan",
            origin_location="Abia",
            created_by=self.owner,
        )
        self.village = Village.objects.create(
            name="Umuahia",
            clan=self.clan,
            location="Abia, Nigeria",
            created_by=self.owner,
        )
        self.family_branch = FamilyBranch.objects.create(
            name="Okafor Main Branch",
            family_name="Okafor",
            clan=self.clan,
            village=self.village,
            community=self.community,
            created_by=self.owner,
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.owner)

    def create_record(self, **overrides):
        data = {
            "title": "Okafor Family Origins",
            "record_type": LineageRecord.RecordType.FAMILY_TREE,
            "summary": "Origins and early migration.",
            "story": "Family story.",
            "visibility": LineageRecord.Visibility.PUBLIC,
            "clan": self.clan,
            "village": self.village,
            "family_branch": self.family_branch,
            "community": self.community,
            "created_by": self.owner,
        }
        data.update(overrides)
        return LineageRecord.objects.create(**data)

    def test_clan_list_requires_authentication(self):
        response = self.client.get(reverse("lineage:clan-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reference_endpoints_return_clans_villages_and_family_branches(self):
        self.authenticate()

        clans_response = self.client.get(reverse("lineage:clan-list"))
        villages_response = self.client.get(
            reverse("lineage:village-list"),
            {"clan_id": self.clan.id},
        )
        branches_response = self.client.get(
            reverse("lineage:family-branch-list"),
            {"community_id": self.community.id},
        )

        self.assertEqual(clans_response.status_code, status.HTTP_200_OK)
        self.assertEqual(villages_response.status_code, status.HTTP_200_OK)
        self.assertEqual(branches_response.status_code, status.HTTP_200_OK)
        self.assertEqual(clans_response.data[0]["name"], self.clan.name)
        self.assertEqual(villages_response.data[0]["name"], self.village.name)
        self.assertEqual(branches_response.data[0]["name"], self.family_branch.name)

    def test_create_lineage_record_with_nested_ancestors_and_history(self):
        self.authenticate()

        response = self.client.post(
            reverse("lineage:record-list-create"),
            {
                "title": "Okafor Family Origins",
                "type": LineageRecord.RecordType.ORAL_HISTORY,
                "summary": "Origins and early migration.",
                "story": "The family migrated across several villages.",
                "source": "Family elder interview",
                "start_year": 1850,
                "end_year": 1950,
                "visibility": LineageRecord.Visibility.PRIVATE,
                "clan_id": str(self.clan.id),
                "village_id": str(self.village.id),
                "family_branch_id": str(self.family_branch.id),
                "community_id": str(self.community.id),
                "allowed_user_ids": [str(self.member.id)],
                "editor_user_ids": [str(self.editor.id)],
                "ancestors": [
                    {
                        "full_name": "Eze Okafor",
                        "gender": "male",
                        "birth_year": 1850,
                        "relationship": "Patriarch",
                        "order": 1,
                    }
                ],
                "historical_records": [
                    {
                        "title": "Interview notes",
                        "description": "Notes from family elder.",
                        "source": "Oral interview",
                        "order": 1,
                    }
                ],
                "metadata": {"region": "South East"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Okafor Family Origins")
        self.assertEqual(response.data["type"], LineageRecord.RecordType.ORAL_HISTORY)
        self.assertEqual(len(response.data["ancestors"]), 1)
        self.assertEqual(len(response.data["historical_records"]), 1)
        self.assertEqual(LineageRecord.objects.count(), 1)
        self.assertEqual(Ancestor.objects.count(), 1)
        self.assertEqual(HistoricalRecord.objects.count(), 1)

    def test_public_records_are_visible_to_authenticated_users(self):
        record = self.create_record(visibility=LineageRecord.Visibility.PUBLIC)
        self.authenticate(self.outsider)

        list_response = self.client.get(reverse("lineage:record-list-create"))
        detail_response = self.client.get(
            reverse("lineage:record-detail", kwargs={"pk": record.pk}),
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

    def test_private_records_require_allowed_user_or_membership(self):
        record = self.create_record(
            visibility=LineageRecord.Visibility.PRIVATE,
            community=None,
        )
        record.allowed_users.add(self.member)

        self.authenticate(self.outsider)
        outsider_response = self.client.get(reverse("lineage:record-list-create"))

        self.authenticate(self.member)
        member_response = self.client.get(reverse("lineage:record-list-create"))

        self.assertEqual(outsider_response.status_code, status.HTTP_200_OK)
        self.assertEqual(outsider_response.data, [])
        self.assertEqual(member_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(member_response.data), 1)

    def test_community_records_are_visible_to_active_members(self):
        self.create_record(
            visibility=LineageRecord.Visibility.COMMUNITY,
            community=self.community,
        )
        self.authenticate(self.member)

        response = self.client.get(reverse("lineage:record-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_member_cannot_patch_but_owner_can_patch_record(self):
        record = self.create_record(
            visibility=LineageRecord.Visibility.COMMUNITY,
            community=self.community,
        )
        self.authenticate(self.member)

        member_response = self.client.patch(
            reverse("lineage:record-detail", kwargs={"pk": record.pk}),
            {"summary": "Member update"},
            format="json",
        )

        self.authenticate(self.owner)
        owner_response = self.client.patch(
            reverse("lineage:record-detail", kwargs={"pk": record.pk}),
            {"summary": "Owner update"},
            format="json",
        )

        self.assertEqual(member_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertEqual(owner_response.data["summary"], "Owner update")

    def test_editor_can_patch_record(self):
        record = self.create_record(visibility=LineageRecord.Visibility.PRIVATE)
        record.editor_users.add(self.editor)
        self.authenticate(self.editor)

        response = self.client.patch(
            reverse("lineage:record-detail", kwargs={"pk": record.pk}),
            {"summary": "Editor update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"], "Editor update")

    def test_community_officer_can_patch_community_record(self):
        CommunityMembership.objects.filter(user=self.member, community=self.community).update(
            role=CommunityMembership.Role.SECRETARY,
        )
        record = self.create_record(
            visibility=LineageRecord.Visibility.COMMUNITY,
            community=self.community,
        )
        self.authenticate(self.member)

        response = self.client.patch(
            reverse("lineage:record-detail", kwargs={"pk": record.pk}),
            {"summary": "Officer update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"], "Officer update")
