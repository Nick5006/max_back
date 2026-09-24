from rest_framework import serializers

from apihandler.models import Appeal

class AppealCreateSerializer(serializers.Serializer):
    apartment_id = serializers.UUIDField()
    title = serializers.CharField(max_length = 200)
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

    management_org = serializers.CharField(
        source="domik.management_org",
        read_only=True,
    )

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
