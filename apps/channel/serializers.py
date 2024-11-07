from rest_framework import serializers
from django.shortcuts import get_object_or_404
from .models import Channel, ChannelMembership, ChannelMessage, ChannelScheduledMessage
from user.serializers import UserSerializer
from user.models import User


class ChannelSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Channel
        fields = ["id", "name", "description", "channel_type", "created_at", "owner"]


class ChannelMembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="user.id", write_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = ChannelMembership
        fields = ["id", "user", "user_id", "role", "joined_at"]

    def create(self, validated_data):
        user_id = validated_data.pop("user")["id"]
        user = get_object_or_404(User, id=user_id)

        return ChannelMembership.objects.create(user=user, **validated_data)


class ChannelMembershipUpdateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ChannelMembership
        fields = ["id", "user", "channel", "role", "joined_at"]
        extra_kwargs = {
            "channel": {"read_only": True},
            "joined_at": {"read_only": True},
        }


class ChannelMessageSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    liked_by = serializers.SerializerMethodField()

    class Meta:
        model = ChannelMessage
        fields = [
            "id",
            "channel",
            "user",
            "text",
            "media",
            "file",
            "liked_by",
            "created_at",
        ]

    def get_liked_by(self, obj):
        return UserSerializer(obj.likes.all(), many=True).data


class ChannelScheduledMessageSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    scheduled_time = serializers.DateTimeField()

    class Meta:
        model = ChannelScheduledMessage
        fields = [
            "id",
            "channel",
            "user",
            "text",
            "media",
            "file",
            "scheduled_time",
            "created_at",
        ]
