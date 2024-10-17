from rest_framework import serializers
from core.settings import SITE_HOST

from .models import Group, GroupMessage, GroupScheduledMessage, GroupPermission
from user.models import User
from user.serializers import UserSerializer


class GroupSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'is_private', 'owner', 'created_at']


class GroupMembershipSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'is_private', 'owner', 'members', 'created_at']


class GroupMessageSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)
    sender = UserSerializer(read_only=True)
    liked_by = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = GroupMessage
        fields = ['id', 'group', 'sender', 'text', 'image', 'file', 'sent_at', 'liked_by', 'likes_count']
        read_only_fields = ['id', 'sent_at', 'likes_count', 'liked_by']

    def get_liked_by(self, obj):
        return UserSerializer(obj.liked_by.all(), many=True).data

    def get_likes_count(self, obj):
        return obj.liked_by.count()

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if representation.get('image'):
            representation['image'] = f"{SITE_HOST}{representation['image']}"

        if representation.get('file'):
            representation['file'] = f"{SITE_HOST}{representation['file']}"

        return representation


class ScheduledMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupScheduledMessage
        fields = ['groups', 'sender', 'text', 'scheduled_time']


class GroupAddMemberSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    class Meta:
        model = Group
        fields = ['members']


class GroupPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPermission
        fields = ['can_send_messages', 'can_send_media']
