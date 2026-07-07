from rest_framework import serializers

from .models import PasswordResetCode, User, UserProfile, build_initials


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "location",
            "bio",
            "family_name",
            "house",
            "village",
            "clan",
            "join_date",
        )
        read_only_fields = ("join_date",)


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "firebase_uid",
            "email",
            "full_name",
            "avatar_initials",
            "phone_number",
            "date_joined",
            "profile",
        )
        read_only_fields = ("id", "firebase_uid", "email", "avatar_initials", "date_joined")


class SessionSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=180, required=False, allow_blank=True)
    name = serializers.CharField(max_length=180, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    location = serializers.CharField(max_length=180, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    family_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    house = serializers.CharField(max_length=120, required=False, allow_blank=True)
    village = serializers.CharField(max_length=120, required=False, allow_blank=True)
    clan = serializers.CharField(max_length=120, required=False, allow_blank=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code_type = serializers.ChoiceField(
        choices=PasswordResetCode.CodeType.choices,
        required=False,
        default=PasswordResetCode.CodeType.NUMERIC,
    )


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)


class UserUpdateSerializer(serializers.ModelSerializer):
    location = serializers.CharField(max_length=180, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    family_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    house = serializers.CharField(max_length=120, required=False, allow_blank=True)
    village = serializers.CharField(max_length=120, required=False, allow_blank=True)
    clan = serializers.CharField(max_length=120, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "full_name",
            "phone_number",
            "location",
            "bio",
            "family_name",
            "house",
            "village",
            "clan",
        )

    def update(self, instance, validated_data):
        profile_fields = {
            "location",
            "bio",
            "family_name",
            "house",
            "village",
            "clan",
        }
        profile_data = {
            field: validated_data.pop(field)
            for field in list(validated_data.keys())
            if field in profile_fields
        }

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if "full_name" in validated_data:
            instance.avatar_initials = build_initials(instance.full_name or instance.email)
        instance.save()

        profile, _ = UserProfile.objects.get_or_create(user=instance)
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()

        return instance
