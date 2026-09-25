from rest_framework import serializers

from apihandler.models import Appeal


class AppealCreateSerializer(serializers.Serializer):
    apartment_id = serializers.UUIDField()
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()


class AppealListSerializer(serializers.ModelSerializer):
    apartment_id = serializers.UUIDField(
        source="apartment.id",
        read_only=True,
    )

    apartment_number = serializers.CharField(
        source="apartment.number",
        read_only=True,
    )

    domik_id = serializers.UUIDField(
        source="domik.id",
        read_only=True,
    )

    domik_address = serializers.CharField(
        source="domik.address",
        read_only=True,
    )

    management_org = serializers.SerializerMethodField()

    class Meta:
        model = Appeal

        fields = (
            "id",
            "title",
            "description",
            "status",
            "created_at",
            "apartment_id",
            "apartment_number",
            "domik_id",
            "domik_address",
            "management_org",
        )

    def get_management_org(self, obj):
        org = obj.domik.management_org
        if org is None:
            return None
        return {"id": str(org.id), "name": org.name}