from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
import logging

from .firebase import verify_id_token
from .services import sync_firebase_user

logger = logging.getLogger(__name__)


class FirebaseAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = get_authorization_header(request).split()

        if not auth_header:
            return None

        if auth_header[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth_header) != 2:
            raise exceptions.AuthenticationFailed("Invalid Authorization header.")

        try:
            token = auth_header[1].decode("utf-8")
        except UnicodeError as exc:
            raise exceptions.AuthenticationFailed("Invalid token encoding.") from exc

        try:
            decoded_token = verify_id_token(token)
        except Exception as exc:
            logger.warning("Firebase token verification failed: %s", exc, exc_info=True)
            raise exceptions.AuthenticationFailed("Your session expired. Please sign in again.") from exc

        user, _ = sync_firebase_user(decoded_token)
        if not user.is_active:
            raise exceptions.PermissionDenied("This user account is disabled.")

        return user, decoded_token

    def authenticate_header(self, request):
        return self.keyword
