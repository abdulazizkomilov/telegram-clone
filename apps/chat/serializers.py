from rest_framework import serializers
from core.settings import SITE_HOST
from .models import Chat, ChatParticipant, Message, ScheduledMessage
from user.serializers import UserSerializer
from user.models import User


class ChatParticipantSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.id')

    class Meta:
        model = ChatParticipant
        fields = ['user', 'joined_at']


class ChatSerializer(serializers.ModelSerializer):
    participants = ChatParticipantSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'owner', 'user', 'created_at', 'participants']


class ChatCreateSerializer(serializers.ModelSerializer):
    participants = ChatParticipantSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    owner_id = serializers.UUIDField(write_only=True)
    user_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'owner', 'user', 'created_at', 'participants', 'owner_id', 'user_id']
        read_only_fields = ['id', 'created_at', 'participants']

    def validate(self, attrs):
        owner_id = attrs.get("owner_id")
        user_id = attrs.get("user_id")

        if owner_id == user_id:
            raise serializers.ValidationError("Owner and user cannot be the same.")

        if not User.objects.filter(id=owner_id).exists():
            raise serializers.ValidationError("Owner does not exist.")

        if not User.objects.filter(id=user_id).exists():
            raise serializers.ValidationError("User does not exist.")

        if Chat.objects.filter(owner_id=owner_id, user_id=user_id).exists():
            raise serializers.ValidationError("Chat between these users already exists.")

        return attrs


class MessageSerializer(serializers.ModelSerializer):
    chat = ChatSerializer(read_only=True)
    sender = UserSerializer(read_only=True)
    liked_by = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'sender', 'text', 'image', 'file', 'sent_at',
            'is_read', 'liked_by', 'likes_count'
        ]

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
        model = ScheduledMessage
        fields = ['chat', 'sender', 'text', 'scheduled_time']
