from rest_framework import serializers

class NotificationSerializer(serializers.Serializer):
    domik_id = serializers.UUIDField()
    title = serializers.CharField(max_length=200)
    text = serializers.CharField()