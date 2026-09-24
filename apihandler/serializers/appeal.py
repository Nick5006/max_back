from rest_framework import serializers

class AppealCreateSerializer(serializers.Serializer):
    apartment_id = serializers.UUIDField()
    title = serializers.CharField(max_length = 200)
    description = serializers.CharField()

