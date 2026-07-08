from django.contrib.auth import get_user_model
from rest_framework import serializers

from communities.models import Community
from communities.permissions import can_view_community

from .models import Ancestor, Clan, FamilyBranch, HistoricalRecord, LineageRecord, Village


User = get_user_model()


class LineageUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    avatar_initials = serializers.CharField()


class LineageCommunitySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    type = serializers.CharField(source="community_type")
    visibility = serializers.CharField()


class ClanSerializer(serializers.ModelSerializer):
    created_by = LineageUserSerializer(read_only=True)

    class Meta:
        model = Clan
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "origin_location",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_by", "created_at", "updated_at")


class VillageSerializer(serializers.ModelSerializer):
    clan = ClanSerializer(read_only=True)
    created_by = LineageUserSerializer(read_only=True)

    class Meta:
        model = Village
        fields = (
            "id",
            "name",
            "slug",
            "clan",
            "location",
            "description",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "clan", "created_by", "created_at", "updated_at")


class FamilyBranchSerializer(serializers.ModelSerializer):
    clan = ClanSerializer(read_only=True)
    village = VillageSerializer(read_only=True)
    community = LineageCommunitySerializer(read_only=True)
    created_by = LineageUserSerializer(read_only=True)

    class Meta:
        model = FamilyBranch
        fields = (
            "id",
            "name",
            "slug",
            "family_name",
            "clan",
            "village",
            "community",
            "description",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "clan",
            "village",
            "community",
            "created_by",
            "created_at",
            "updated_at",
        )


class AncestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ancestor
        fields = (
            "id",
            "full_name",
            "gender",
            "birth_year",
            "death_year",
            "relationship",
            "notes",
            "order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class HistoricalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalRecord
        fields = (
            "id",
            "title",
            "description",
            "record_date",
            "source",
            "file_url",
            "storage_path",
            "order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class LineageRecordSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        source="record_type",
        choices=LineageRecord.RecordType.choices,
    )
    clan = ClanSerializer(read_only=True)
    village = VillageSerializer(read_only=True)
    family_branch = FamilyBranchSerializer(read_only=True)
    community = LineageCommunitySerializer(read_only=True)
    created_by = LineageUserSerializer(read_only=True)
    allowed_users = LineageUserSerializer(many=True, read_only=True)
    editor_users = LineageUserSerializer(many=True, read_only=True)
    ancestors = AncestorSerializer(many=True, required=False)
    historical_records = HistoricalRecordSerializer(many=True, required=False)
    clan_id = serializers.PrimaryKeyRelatedField(
        queryset=Clan.objects.all(),
        source="clan",
        write_only=True,
        required=False,
        allow_null=True,
    )
    village_id = serializers.PrimaryKeyRelatedField(
        queryset=Village.objects.all(),
        source="village",
        write_only=True,
        required=False,
        allow_null=True,
    )
    family_branch_id = serializers.PrimaryKeyRelatedField(
        queryset=FamilyBranch.objects.all(),
        source="family_branch",
        write_only=True,
        required=False,
        allow_null=True,
    )
    community_id = serializers.PrimaryKeyRelatedField(
        queryset=Community.objects.all(),
        source="community",
        write_only=True,
        required=False,
        allow_null=True,
    )
    allowed_user_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="allowed_users",
        many=True,
        write_only=True,
        required=False,
    )
    editor_user_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="editor_users",
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = LineageRecord
        fields = (
            "id",
            "title",
            "type",
            "summary",
            "story",
            "source",
            "start_year",
            "end_year",
            "visibility",
            "status",
            "clan",
            "clan_id",
            "village",
            "village_id",
            "family_branch",
            "family_branch_id",
            "community",
            "community_id",
            "created_by",
            "allowed_users",
            "allowed_user_ids",
            "editor_users",
            "editor_user_ids",
            "ancestors",
            "historical_records",
            "metadata",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        community = attrs.get("community", getattr(self.instance, "community", None))
        clan = attrs.get("clan", getattr(self.instance, "clan", None))
        village = attrs.get("village", getattr(self.instance, "village", None))
        family_branch = attrs.get("family_branch", getattr(self.instance, "family_branch", None))

        if "community" in attrs and community and request and not can_view_community(request.user, community):
            raise serializers.ValidationError("You do not have access to this community.")

        if village and clan and village.clan_id and village.clan_id != clan.id:
            raise serializers.ValidationError("The selected village does not belong to the selected clan.")

        if family_branch:
            if clan and family_branch.clan_id and family_branch.clan_id != clan.id:
                raise serializers.ValidationError("The selected family branch does not belong to the selected clan.")
            if village and family_branch.village_id and family_branch.village_id != village.id:
                raise serializers.ValidationError("The selected family branch does not belong to the selected village.")
            if community and family_branch.community_id and family_branch.community_id != community.id:
                raise serializers.ValidationError("The selected family branch does not belong to the selected community.")

        return attrs

    def create(self, validated_data):
        ancestors_data = validated_data.pop("ancestors", [])
        historical_records_data = validated_data.pop("historical_records", [])
        allowed_users = validated_data.pop("allowed_users", [])
        editor_users = validated_data.pop("editor_users", [])

        lineage_record = LineageRecord.objects.create(**validated_data)
        lineage_record.allowed_users.set(allowed_users)
        lineage_record.editor_users.set(editor_users)
        self._replace_ancestors(lineage_record, ancestors_data)
        self._replace_historical_records(lineage_record, historical_records_data)
        return lineage_record

    def update(self, instance, validated_data):
        ancestors_data = validated_data.pop("ancestors", None)
        historical_records_data = validated_data.pop("historical_records", None)
        allowed_users = validated_data.pop("allowed_users", None)
        editor_users = validated_data.pop("editor_users", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if allowed_users is not None:
            instance.allowed_users.set(allowed_users)
        if editor_users is not None:
            instance.editor_users.set(editor_users)
        if ancestors_data is not None:
            self._replace_ancestors(instance, ancestors_data)
        if historical_records_data is not None:
            self._replace_historical_records(instance, historical_records_data)

        return instance

    def _replace_ancestors(self, lineage_record, ancestors_data):
        lineage_record.ancestors.all().delete()
        Ancestor.objects.bulk_create(
            Ancestor(lineage_record=lineage_record, **ancestor)
            for ancestor in ancestors_data
        )

    def _replace_historical_records(self, lineage_record, historical_records_data):
        lineage_record.historical_records.all().delete()
        HistoricalRecord.objects.bulk_create(
            HistoricalRecord(lineage_record=lineage_record, **historical_record)
            for historical_record in historical_records_data
        )
