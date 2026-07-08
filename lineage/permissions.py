from django.db.models import Q

from communities.models import CommunityMembership
from communities.permissions import can_manage_community, get_active_membership

from .models import LineageRecord


def visible_lineage_records_for_user(user):
    return LineageRecord.objects.filter(
        Q(visibility=LineageRecord.Visibility.PUBLIC)
        | Q(created_by=user)
        | Q(allowed_users=user)
        | Q(editor_users=user)
        | Q(
            community__memberships__user=user,
            community__memberships__status=CommunityMembership.Status.ACTIVE,
        ),
        status=LineageRecord.Status.ACTIVE,
    ).distinct()


def can_view_lineage_record(user, record):
    if record.status != LineageRecord.Status.ACTIVE:
        return record.created_by_id == user.id

    if record.visibility == LineageRecord.Visibility.PUBLIC:
        return True

    if record.created_by_id == user.id:
        return True

    if record.allowed_users.filter(pk=user.pk).exists():
        return True

    if record.editor_users.filter(pk=user.pk).exists():
        return True

    if record.community_id and get_active_membership(user, record.community):
        return True

    return False


def can_edit_lineage_record(user, record):
    if record.created_by_id == user.id:
        return True

    if record.editor_users.filter(pk=user.pk).exists():
        return True

    if record.community_id and can_manage_community(user, record.community):
        return True

    return False
