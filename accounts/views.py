from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    SessionSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .services import confirm_password_reset, request_password_reset_code, sync_firebase_user


class SessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, created = sync_firebase_user(
            request.auth,
            profile_data=serializer.validated_data,
        )
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(UserSerializer(user).data, status=response_status)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_code, code = request_password_reset_code(
            email=serializer.validated_data["email"],
            code_type=serializer.validated_data["code_type"],
        )
        return Response(
            {
                "detail": "If an account exists for this email, a reset code has been generated.",
                "email": reset_code.email,
                "code_type": reset_code.code_type,
                "code_length": 6,
                "expires_at": reset_code.expires_at,
                "expires_in_seconds": 600,
                "reset_code": code,
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = confirm_password_reset(
            email=serializer.validated_data["email"],
            code=serializer.validated_data["code"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response(
            {
                "detail": "Password reset successful. The user can now log in with the new password.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )
