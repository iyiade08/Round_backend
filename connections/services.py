from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError

from communities.models import Community, CommunityMembership

from .models import Connection, ConnectionRequest


User = get_user_model()


def ordered_user_pair(user_one, user_two):
    if str(user_one.id) <= str(user_two.id):
        return user_one, user_two
    return user_two, user_one


def get_connection_between(user_one, user_two):
    return Connection.objects.filter(
        Q(user_a=user_one, user_b=user_two) | Q(user_a=user_two, user_b=user_one)
    ).first()


def get_connected_user_ids(user):
    connections = Connection.objects.filter(Q(user_a=user) | Q(user_b=user))
    connected_ids = set()
    for connection in connections:
        if connection.user_a_id == user.id:
            connected_ids.add(connection.user_b_id)
        else:
            connected_ids.add(connection.user_a_id)
    return connected_ids


def get_pending_request_between(user_one, user_two):
    return ConnectionRequest.objects.filter(
        Q(sender=user_one, receiver=user_two) | Q(sender=user_two, receiver=user_one),
        status=ConnectionRequest.Status.PENDING,
    ).first()


def send_connection_request(*, sender, receiver, message=""):
    if sender.id == receiver.id:
        raise ValidationError("You cannot send a connection request to yourself.")

    if not receiver.is_active:
        raise ValidationError("This user is not available for connection requests.")

    if get_connection_between(sender, receiver):
        raise ValidationError("You are already connected to this user.")

    if get_pending_request_between(sender, receiver):
        raise ValidationError("A pending connection request already exists.")

    return ConnectionRequest.objects.create(
        sender=sender,
        receiver=receiver,
        message=message,
    )


@transaction.atomic
def accept_connection_request(*, user, connection_request):
    if connection_request.receiver_id != user.id:
        raise PermissionDenied("Only the request receiver can accept this connection request.")

    if connection_request.status != ConnectionRequest.Status.PENDING:
        raise ValidationError("Only pending connection requests can be accepted.")

    user_a, user_b = ordered_user_pair(connection_request.sender, connection_request.receiver)
    connection, _ = Connection.objects.get_or_create(user_a=user_a, user_b=user_b)
    connection_request.mark_responded(ConnectionRequest.Status.ACCEPTED)
    return connection


def reject_connection_request(*, user, connection_request):
    if connection_request.receiver_id != user.id:
        raise PermissionDenied("Only the request receiver can reject this connection request.")

    if connection_request.status != ConnectionRequest.Status.PENDING:
        raise ValidationError("Only pending connection requests can be rejected.")

    connection_request.mark_responded(ConnectionRequest.Status.REJECTED)
    return connection_request


def delete_connection(*, user, connection):
    if connection.user_a_id != user.id and connection.user_b_id != user.id:
        raise PermissionDenied("You can only remove your own connections.")

    connection.delete()


def get_connection_status(current_user, target_user):
    if current_user.id == target_user.id:
        return "self"

    if get_connection_between(current_user, target_user):
        return "connected"

    pending_request = get_pending_request_between(current_user, target_user)
    if not pending_request:
        return "none"

    if pending_request.sender_id == current_user.id:
        return "pending_sent"
    return "pending_received"


def get_recommendations_for_user(user, limit=20):
    candidates = list(
        User.objects.filter(is_active=True)
        .exclude(pk=user.pk)
        .select_related("profile")
        .order_by("full_name", "email")
    )

    connected_ids = get_connected_user_ids(user)
    pending_requests = ConnectionRequest.objects.filter(
        Q(sender=user) | Q(receiver=user),
        status=ConnectionRequest.Status.PENDING,
    )
    pending_user_ids = {
        request.receiver_id if request.sender_id == user.id else request.sender_id
        for request in pending_requests
    }
    excluded_ids = connected_ids | pending_user_ids
    candidates = [candidate for candidate in candidates if candidate.id not in excluded_ids]
    candidate_ids = [candidate.id for candidate in candidates]

    current_profile = getattr(user, "profile", None)
    current_memberships = CommunityMembership.objects.filter(
        user=user,
        status=CommunityMembership.Status.ACTIVE,
        community__status=Community.Status.ACTIVE,
    ).select_related("community")
    current_communities = {
        membership.community_id: membership.community.name
        for membership in current_memberships
    }

    candidate_communities = defaultdict(dict)
    memberships = CommunityMembership.objects.filter(
        user_id__in=candidate_ids,
        status=CommunityMembership.Status.ACTIVE,
        community__status=Community.Status.ACTIVE,
    ).select_related("community")
    for membership in memberships:
        candidate_communities[membership.user_id][membership.community_id] = membership.community.name

    user_connected_ids = get_connected_user_ids(user)
    candidate_connection_map = defaultdict(set)
    candidate_connections = Connection.objects.filter(
        Q(user_a_id__in=candidate_ids) | Q(user_b_id__in=candidate_ids)
    )
    for connection in candidate_connections:
        candidate_connection_map[connection.user_a_id].add(connection.user_b_id)
        candidate_connection_map[connection.user_b_id].add(connection.user_a_id)

    recommendations = []
    for candidate in candidates:
        candidate_profile = getattr(candidate, "profile", None)
        score = 0
        reasons = []

        if _same_profile_value(current_profile, candidate_profile, "family_name"):
            score += 30
            reasons.append("Same family name")

        if _same_profile_value(current_profile, candidate_profile, "clan"):
            score += 25
            reasons.append("Same clan")

        if _same_profile_value(current_profile, candidate_profile, "village"):
            score += 20
            reasons.append("Same village")

        shared_community_ids = set(current_communities) & set(candidate_communities[candidate.id])
        if shared_community_ids:
            shared_names = sorted(current_communities[community_id] for community_id in shared_community_ids)
            score += 15 * len(shared_community_ids)
            reasons.append(f"Shared community: {', '.join(shared_names)}")

        mutual_connection_ids = user_connected_ids & candidate_connection_map[candidate.id]
        if mutual_connection_ids:
            score += 10 * len(mutual_connection_ids)
            reasons.append(f"Mutual connections: {len(mutual_connection_ids)}")

        if score > 0:
            recommendations.append(
                {
                    "user": candidate,
                    "score": score,
                    "reasons": reasons,
                }
            )

    return sorted(
        recommendations,
        key=lambda item: (-item["score"], item["user"].full_name.lower(), item["user"].email.lower()),
    )[:limit]


def _same_profile_value(profile_one, profile_two, field):
    value_one = (getattr(profile_one, field, "") or "").strip().lower()
    value_two = (getattr(profile_two, field, "") or "").strip().lower()
    return bool(value_one and value_two and value_one == value_two)
