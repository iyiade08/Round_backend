from communities.permissions import can_manage_community, can_view_community, get_active_membership


def can_view_community_content(user, community):
    return can_view_community(user, community)


def can_create_announcement(user, community):
    return can_manage_community(user, community)


def can_create_member_content(user, community):
    return get_active_membership(user, community) is not None
