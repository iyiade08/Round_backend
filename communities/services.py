from django.db import transaction

from .models import Community, CommunityMembership


@transaction.atomic
def create_community(*, user, community_data):
    community = Community.objects.create(created_by=user, **community_data)
    CommunityMembership.objects.create(
        user=user,
        community=community,
        role=CommunityMembership.Role.OWNER,
        status=CommunityMembership.Status.ACTIVE,
    )
    return community


@transaction.atomic
def join_or_request_community(*, user, community):
    membership, created = CommunityMembership.objects.get_or_create(
        user=user,
        community=community,
        defaults={
            "role": CommunityMembership.Role.MEMBER,
            "status": CommunityMembership.Status.ACTIVE
            if community.visibility == Community.Visibility.PUBLIC
            else CommunityMembership.Status.REQUESTED,
        },
    )

    if not created:
        if membership.status in {
            CommunityMembership.Status.LEFT,
            CommunityMembership.Status.INVITED,
        }:
            membership.status = CommunityMembership.Status.ACTIVE
            membership.role = membership.role or CommunityMembership.Role.MEMBER
            membership.save(update_fields=["status", "role", "updated_at"])
        elif (
            membership.status == CommunityMembership.Status.REQUESTED
            and community.visibility == Community.Visibility.PUBLIC
        ):
            membership.status = CommunityMembership.Status.ACTIVE
            membership.save(update_fields=["status", "updated_at"])

    return membership
