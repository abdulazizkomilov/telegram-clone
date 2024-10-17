from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from share.permissions import IsOwner
from .models import Chat, Message
from .serializers import ChatCreateSerializer, MessageSerializer


class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(owner=user).union(Chat.objects.filter(user=user))


class ChatView(generics.RetrieveDestroyAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatCreateSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    http_method_names = ['get', 'delete']


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(chat_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        chat_id = self.kwargs['pk']
        chat = Chat.objects.get(id=chat_id)

        message = serializer.save(sender=self.request.user, chat=chat)

        if message.file or message.image:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{message.chat.id}',
                {
                    'type': 'chat_message',
                    'message_id': str(message.id),
                    'sender': {
                        'id': str(message.sender.id),
                        'user_name': str(message.sender.username),
                    },
                    'text': message.text,
                    'image': message.image.url if message.image.url else None,
                    'file': message.file if message.file else None,
                    'sent_at': message.sent_at.isoformat(),
                }
            )
