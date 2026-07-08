from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from communities.models import Community, CommunityMembership

from .models import Announcement, CommunityBusiness, ForumPost, ForumReply, GalleryItem


class CommunityHubApiTests(APITestCase):
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

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.owner)

    def test_announcement_list_requires_community_access(self):
        Announcement.objects.create(
            community=self.community,
            title="Family meeting",
            body="Meeting this weekend.",
            created_by=self.owner,
        )
        self.authenticate(self.outsider)

        response = self.client.get(
            reverse("feeds:community-announcements", kwargs={"community_id": self.community.pk}),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_officers_can_create_announcements(self):
        self.authenticate(self.member)

        member_response = self.client.post(
            reverse("feeds:community-announcements", kwargs={"community_id": self.community.pk}),
            {
                "title": "Family meeting",
                "body": "Meeting this weekend.",
            },
            format="json",
        )

        self.authenticate(self.owner)
        owner_response = self.client.post(
            reverse("feeds:community-announcements", kwargs={"community_id": self.community.pk}),
            {
                "title": "Family meeting",
                "body": "Meeting this weekend.",
                "category": "meeting",
                "is_pinned": True,
            },
            format="json",
        )

        self.assertEqual(member_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(owner_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(owner_response.data["title"], "Family meeting")
        self.assertTrue(owner_response.data["is_pinned"])

    def test_active_member_can_create_and_list_forum_posts(self):
        self.authenticate(self.member)

        create_response = self.client.post(
            reverse("feeds:community-forum-posts", kwargs={"community_id": self.community.pk}),
            {
                "title": "Who has the old photos?",
                "body": "Please share any photos from the reunion.",
                "category": "family-history",
            },
            format="json",
        )
        list_response = self.client.get(
            reverse("feeds:community-forum-posts", kwargs={"community_id": self.community.pk}),
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data[0]["title"], "Who has the old photos?")
        self.assertEqual(list_response.data[0]["replies_count"], 0)

    def test_outsider_cannot_create_forum_post_in_private_community(self):
        self.authenticate(self.outsider)

        response = self.client.post(
            reverse("feeds:community-forum-posts", kwargs={"community_id": self.community.pk}),
            {
                "title": "Hello",
                "body": "Trying to post.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_create_and_list_forum_replies(self):
        post = ForumPost.objects.create(
            community=self.community,
            title="Family question",
            body="Who knows this story?",
            author=self.owner,
        )
        self.authenticate(self.member)

        create_response = self.client.post(
            reverse("feeds:forum-post-replies", kwargs={"post_id": post.pk}),
            {"body": "I can ask my grandmother."},
            format="json",
        )
        list_response = self.client.get(
            reverse("feeds:forum-post-replies", kwargs={"post_id": post.pk}),
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data[0]["body"], "I can ask my grandmother.")
        self.assertEqual(ForumReply.objects.count(), 1)

    def test_closed_forum_post_rejects_replies(self):
        post = ForumPost.objects.create(
            community=self.community,
            title="Closed discussion",
            body="No more replies.",
            author=self.owner,
            status=ForumPost.Status.CLOSED,
        )
        self.authenticate(self.member)

        response = self.client.post(
            reverse("feeds:forum-post-replies", kwargs={"post_id": post.pk}),
            {"body": "Trying anyway."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_member_can_create_gallery_item_with_storage_metadata(self):
        self.authenticate(self.member)

        response = self.client.post(
            reverse("feeds:community-gallery", kwargs={"community_id": self.community.pk}),
            {
                "title": "Reunion photo",
                "caption": "Family reunion photo.",
                "media_type": GalleryItem.MediaType.IMAGE,
                "file_url": "https://example.com/reunion.jpg",
                "storage_path": "communities/reunion.jpg",
                "metadata": {"width": 1200, "height": 800},
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["file_url"], "https://example.com/reunion.jpg")
        self.assertEqual(response.data["metadata"]["width"], 1200)
        self.assertEqual(GalleryItem.objects.count(), 1)

    def test_member_can_create_business_listing(self):
        self.authenticate(self.member)

        response = self.client.post(
            reverse("feeds:community-commerce", kwargs={"community_id": self.community.pk}),
            {
                "name": "Okafor Farms",
                "category": "Agriculture",
                "description": "Family-owned produce business.",
                "phone_number": "+2348000000000",
                "email": "farms@example.com",
                "website": "https://example.com",
                "address": "Lagos, Nigeria",
                "logo_url": "https://example.com/logo.png",
                "storage_path": "businesses/logo.png",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Okafor Farms")
        self.assertEqual(CommunityBusiness.objects.count(), 1)

    def test_public_community_content_is_readable_but_posting_still_requires_membership(self):
        public_community = Community.objects.create(
            name="Public Neighborhood",
            community_type=Community.CommunityType.NEIGHBORHOOD,
            visibility=Community.Visibility.PUBLIC,
            created_by=self.owner,
        )
        Announcement.objects.create(
            community=public_community,
            title="Welcome",
            body="Public update.",
            created_by=self.owner,
        )
        self.authenticate(self.outsider)

        list_response = self.client.get(
            reverse("feeds:community-announcements", kwargs={"community_id": public_community.pk}),
        )
        create_response = self.client.post(
            reverse("feeds:community-forum-posts", kwargs={"community_id": public_community.pk}),
            {
                "title": "Hello",
                "body": "Trying to post before joining.",
            },
            format="json",
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
