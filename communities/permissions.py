from django.db.models import Q

from .models import Community, CommunityMembership


MANAGER_ROLES = {
    CommunityMembership.Role.OWNER,
    CommunityMembership.Role.PRESIDENT,
    CommunityMembership.Role.SECRETARY,
    CommunityMembership.Role.TREASURER,
    CommunityMembership.Role.OFFICER,
}


def visible_communities_for_user(user):
    return Community.objects.filter(
        Q(visibility=Community.Visibility.PUBLIC)
        | Q(memberships__user=user, memberships__status=CommunityMembership.Status.ACTIVE),
        status=Community.Status.ACTIVE,
    ).distinct()


def get_active_membership(user, community):
    if not user or not user.is_authenticated:
        return None

    return CommunityMembership.objects.filter(
        user=user,
        community=community,
        status=CommunityMembership.Status.ACTIVE,
    ).first()


def can_view_community(user, community):
    if community.status != Community.Status.ACTIVE:
        return False
    if community.visibility == Community.Visibility.PUBLIC:
        return True
    return get_active_membership(user, community) is not None


def can_manage_community(user, community):
    membership = get_active_membership(user, community)
    return bool(membership and membership.role in MANAGER_ROLES)
