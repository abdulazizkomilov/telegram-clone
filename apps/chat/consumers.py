from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer.generics import ObserverModelInstanceMixin
from django.contrib.auth.models import AnonymousUser
from djangochannelsrestframework.observer.generics import action

from .models import Chat, ChatParticipant, Message, ScheduledMessage
from .serializers import ChatSerializer, MessageSerializer
from user.models import User
from user.serializers import UserSerializer


class ChatConsumer(
    ObserverModelInstanceMixin, GenericAsyncAPIConsumer, AsyncJsonWebsocketConsumer
):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    lookup_field = "pk"

    async def connect(self):
        self.user = self.scope.get("user", AnonymousUser())
        self.chat_id = self.scope["url_route"]["kwargs"]["pk"]
        self.chat = await self.get_chat(self.chat_id)
        self.participants = await self.current_users(self.chat)

        if not self.user.is_authenticated:
            return await self.close()

        if not self.chat:
            return await self.close()

        if self.user.id not in {self.chat.owner_id, self.chat.user_id}:
            return await self.close()

        await self.channel_layer.group_add(f"chat__{self.chat_id}", self.channel_name)
        await self.add_user_to_chat(self.chat_id)
        await self.accept()
        await self.update_user_status(is_online=True)
        await self.notify_users()
        await self.get_messages(self.chat_id)

    async def disconnect(self, code):
        if self.user.is_authenticated:
            await self.remove_user_from_chat(self.chat_id)
            await self.update_user_status(is_online=False)
            await self.notify_users()
            await self.channel_layer.group_discard(
                f"chat__{self.chat_id}", self.channel_name
            )
        await super().disconnect(code)

    async def notify_users(self):
        participants = await self.current_users(self.chat)
        users = await self.serialize_users(participants)
        await self.channel_layer.group_send(
            f"chat__{self.chat_id}", {"type": "update_users", "users": users}
        )

    async def update_users(self, event):
        await self.send_json({"users": event["users"]})

    async def chat_message(self, event):
        await self.send_json({"action": "new_message", "data": event["text"]})

    async def message_liked(self, event):
        await self.send_json({"action": "message_liked", "data": event["message"]})

    async def message_unliked(self, event):
        await self.send_json({"action": "message_unliked", "data": event["message"]})

    @action()
    async def create_message(self, pk, data, **kwargs):
        chat = await self.get_chat(pk)
        if not chat:
            return

        user = self.scope["user"]
        recipient = await self.get_recipient(chat, user)
        if not recipient:
            return

        message = await self.save_message(chat, user, data)
        serialized_message = await self.serialize_message(message)

        await self.channel_layer.group_send(
            f"chat__{pk}", {"type": "chat_message", "text": serialized_message}
        )

    @action()
    async def get_messages(self, pk, **kwargs):
        messages = await self.fetch_messages(pk)
        serialized_messages = await self.serialize_messages(messages)

        await self.send_json(
            {"action": "get_messages", "messages": serialized_messages}
        )

    @action()
    async def like_message(self, message_id, **kwargs):
        user = self.scope["user"]
        message = await self.get_message(message_id)
        if message:
            await self.add_like(message, user)
            serialized_message = await self.serialize_message(message)
            await self.channel_layer.group_send(
                f"chat__{message.chat.id}",
                {"type": "message_liked", "message": serialized_message},
            )

    @action()
    async def unlike_message(self, message_id, **kwargs):
        user = self.scope["user"]
        message = await self.get_message(message_id)
        if message:
            await self.remove_like(message, user)
            serialized_message = await self.serialize_message(message)
            await self.channel_layer.group_send(
                f"chat__{message.chat.id}",
                {"type": "message_unliked", "message": serialized_message},
            )

    @action()
    async def schedule_message(self, pk, data, **kwargs):
        chat = await self.get_chat(pk)
        if not chat:
            return

        user = self.scope["user"]
        scheduled_time = data.get("scheduled_time")
        if scheduled_time:
            await self.save_scheduled_message(chat, user, data)

    @database_sync_to_async
    def fetch_messages(self, pk: int):
        try:
            chat = Chat.objects.get(pk=pk)
            return list(chat.messages.order_by("sent_at"))
        except Chat.DoesNotExist:
            return []

    @database_sync_to_async
    def serialize_messages(self, messages):
        return MessageSerializer(messages, many=True, context={"user": self.user}).data

    @database_sync_to_async
    def serialize_message(self, message):
        return MessageSerializer(message).data

    @database_sync_to_async
    def save_scheduled_message(self, chat: Chat, user: User, data: dict):
        scheduled_time = data.get("scheduled_time")

        return ScheduledMessage.objects.create(
            chat=chat, sender=user, text=data.get("text"), scheduled_time=scheduled_time
        )

    @database_sync_to_async
    def get_chat(self, pk: int):
        try:
            return Chat.objects.get(pk=pk)
        except Chat.DoesNotExist:
            return None

    @database_sync_to_async
    def current_users(self, chat: Chat):
        participants = ChatParticipant.objects.filter(chat=chat).select_related("user")
        return [UserSerializer(participant.user).data for participant in participants]

    @database_sync_to_async
    def remove_user_from_chat(self, chat_id: int):
        ChatParticipant.objects.filter(user=self.user, chat_id=chat_id).delete()

    @database_sync_to_async
    def add_user_to_chat(self, chat_id: int):
        chat = Chat.objects.get(pk=chat_id)
        if not ChatParticipant.objects.filter(user=self.user, chat=chat).exists():
            ChatParticipant.objects.create(user=self.user, chat=chat)

    @database_sync_to_async
    def save_message(self, chat: Chat, user: User, data: dict):
        valid_keys = {"text", "image", "file"}
        message_data = {key: data.get(key) for key in valid_keys if data.get(key)}

        message = Message.objects.create(chat=chat, sender=user, **message_data)
        return message

    @database_sync_to_async
    def get_message(self, message_id):
        try:
            return Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def add_like(self, message, user):
        message.liked_by.add(user)
        message.save()

    @database_sync_to_async
    def remove_like(self, message, user):
        message.liked_by.remove(user)
        message.save()

    @database_sync_to_async
    def get_recipient(self, chat: Chat, user: User):
        if chat.owner == user:
            return chat.user
        elif chat.user == user:
            return chat.owner
        return None

    @database_sync_to_async
    def serialize_users(self, users):
        return UserSerializer(users, many=True).data

    @database_sync_to_async
    def update_user_status(self, is_online):
        self.user.is_online = is_online
        self.user.update_last_seen()
        self.user.save()


# class UserConsumer(
#     mixins.ListModelMixin,
#     mixins.RetrieveModelMixin,
#     mixins.PatchModelMixin,
#     mixins.UpdateModelMixin,
#     mixins.CreateModelMixin,
#     mixins.DeleteModelMixin,
#     GenericAsyncAPIConsumer,
# ):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
