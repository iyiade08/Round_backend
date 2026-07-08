from django.db.models import Q

from communities.models import Community, CommunityMembership
from communities.permissions import can_manage_community, can_view_community

from .models import Event


def visible_events_for_user(user):
    return Event.objects.filter(
        Q(community__status=Community.Status.ACTIVE)
        & (
            Q(status=Event.Status.PUBLISHED)
            & (
                Q(community__visibility=Community.Visibility.PUBLIC)
                | Q(
                    community__memberships__user=user,
                    community__memberships__status=CommunityMembership.Status.ACTIVE,
                )
            )
            | Q(created_by=user)
            | Q(
                community__memberships__user=user,
                community__memberships__status=CommunityMembership.Status.ACTIVE,
                community__memberships__role__in=[
                    CommunityMembership.Role.OWNER,
                    CommunityMembership.Role.PRESIDENT,
                    CommunityMembership.Role.SECRETARY,
                    CommunityMembership.Role.TREASURER,
                    CommunityMembership.Role.OFFICER,
                ],
            )
        )
    ).distinct()


def can_view_event(user, event):
    if event.created_by_id == user.id:
        return True

    if can_manage_community(user, event.community):
        return True

    if event.status != Event.Status.PUBLISHED:
        return False

    return can_view_community(user, event.community)


def can_create_event(user, community):
    return can_manage_community(user, community)


def can_update_event(user, event):
    return event.created_by_id == user.id or can_manage_community(user, event.community)


def can_rsvp_event(user, event):
    return event.status == Event.Status.PUBLISHED and can_view_event(user, event)
