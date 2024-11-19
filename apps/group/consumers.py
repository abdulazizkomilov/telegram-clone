from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer.generics import action
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import sync_to_async
from share.tasks import send_push_notification

from .models import (
    Group,
    GroupMessage,
    GroupParticipant,
    GroupScheduledMessage,
    GroupPermission,
)
from .serializers import GroupMessageSerializer
from user.models import User
from user.serializers import UserSerializer


class GroupConsumer(GenericAsyncAPIConsumer, AsyncJsonWebsocketConsumer):
    queryset = Group.objects.all()
    serializer_class = GroupMessageSerializer
    lookup_field = "pk"

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get("user", AnonymousUser())
        self.group_id = self.scope["url_route"]["kwargs"]["pk"]

        if not (await self.is_authenticated() and await self.has_group_access()):
            await self.close()
            return

        await self.channel_layer.group_add(f"group__{self.group_id}", self.channel_name)
        await self.accept()

        await self.add_user_to_group()
        await self.update_user_status(is_online=True)
        await self.notify_group_users()
        await self.get_messages(self.group_id)

    async def disconnect(self, code):
        """Handle WebSocket disconnection."""
        if await self.is_authenticated():
            await self.remove_user_from_group()
            await self.update_user_status(is_online=False)
            await self.notify_group_users()

        await self.channel_layer.group_discard(
            f"group__{self.group_id}", self.channel_name
        )
        await super().disconnect(code)

    async def notify_group_users(self):
        """Notify group members about user status changes."""
        group_members = await self.get_group_members()
        await self.channel_layer.group_send(
            f"group__{self.group_id}",
            {
                "type": "update_group_users",
                "users": group_members,
            },
        )

    async def update_group_users(self, event: dict):
        """Send updated user list to the client."""
        await self.send_json({"users": event["users"]})

    async def group_message(self, event):
        """Send new group message to clients."""
        await self.send_json({"action": "new_message", "data": event["text"]})

    async def message_liked(self, event):
        await self.send_json({"action": "message_liked", "data": event["message"]})

    async def message_unliked(self, event):
        await self.send_json({"action": "message_unliked", "data": event["message"]})

    @action()
    async def get_messages(self, pk, **kwargs):
        messages = await self.fetch_group_messages(pk)
        serialized_messages = await self.serialize_messages(messages)

        await self.send_json(
            {"action": "get_messages", "messages": serialized_messages}
        )

    @action()
    async def create_message(self, pk, data, **kwargs):
        """Create and broadcast a new message."""
        if not await self.is_user_group_member():
            await self.send_json(
                {"detail": "You are not a member of this group. Please join first."}
            )
            return

        if not await self.can_send_message(self.group.id):
            await self.send_json(
                {"detail": "You do not have permission to send messages."}
            )
            return

        message = await self.save_message(self.group, self.user, data)
        serialized_message = await self.serialize_message(message)

        await self.channel_layer.group_send(
            f"group__{pk}",
            {
                "type": "group_message",
                "text": serialized_message,
            },
        )

        group_members = await self.get_group_members()

        for member_data in group_members:
            user = await self.get_user(member_data["id"])

            if user.is_online is False:
                try:
                    user_notification_pref = await sync_to_async(
                        lambda: getattr(user, "notification_preference", None)
                    )()

                    if (
                        user_notification_pref is not None
                        and user_notification_pref.notifications_enabled
                    ):
                        device_token = await sync_to_async(
                            lambda: user_notification_pref.device_token
                        )()
                        send_push_notification.delay(
                            token=device_token,
                            title="New Message in Group",
                            body=message.text,
                        )
                except Exception as e:
                    print(f"Error: {e}")

    @action()
    async def get_group_messages(self, pk, **kwargs):
        """Retrieve and send group messages to the client."""
        messages = await self.fetch_group_messages(pk)
        serialized_messages = await self.serialize_messages(messages)

        await self.send_json(
            {
                "action": "get_group_messages",
                "messages": serialized_messages,
            }
        )

    @action()
    async def schedule_message(self, data, **kwargs):
        if not await self.is_user_group_member():
            await self.send_json(
                {"detail": "You are not a member of this group. Please join first."}
            )
            return

        group = await self.get_group()
        if not group:
            return

        user = self.scope["user"]
        scheduled_time = data.get("scheduled_time")
        if scheduled_time:
            await self.save_scheduled_message(group, user, data)

    @action()
    async def like_message(self, message_id, **kwargs):
        if not await self.is_user_group_member():
            await self.send_json(
                {"detail": "You are not a member of this group. Please join first."}
            )
            return

        message = await self.get_message(message_id)
        if message:
            await self.add_like(message, self.user)
            serialized_message = await self.serialize_message(message)
            await self.channel_layer.group_send(
                f"group__{message.group.id}",
                {"type": "message_liked", "message": serialized_message},
            )

    @action()
    async def unlike_message(self, message_id, **kwargs):
        if not await self.is_user_group_member():
            await self.send_json({"detail": "You are not a member of this group."})
            return

        message = await self.get_message(message_id)
        if message:
            await self.remove_like(message, self.user)
            serialized_message = await self.serialize_message(message)
            await self.channel_layer.group_send(
                f"group__{message.group.id}",
                {"type": "message_unliked", "message": serialized_message},
            )

    @database_sync_to_async
    def get_group(self):
        """Retrieve group by ID."""
        return Group.objects.filter(pk=self.group_id).first()

    @database_sync_to_async
    def get_user(self, user_id):
        """Retrieve a user by ID."""
        return User.objects.get(id=user_id)

    @database_sync_to_async
    def get_message(self, message_id):
        try:
            return GroupMessage.objects.get(id=message_id)
        except GroupMessage.DoesNotExist:
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
    def save_scheduled_message(self, group: Group, user: User, data: dict):
        scheduled_time = data.get("scheduled_time")
        if isinstance(scheduled_time, str):
            scheduled_time = timezone.datetime.strptime(
                scheduled_time, "%Y-%m-%dT%H:%M:%SZ"
            )
            scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)

        scheduled_time = scheduled_time - timedelta(hours=5)

        return GroupScheduledMessage.objects.create(
            group=group,
            sender=user,
            text=data.get("text"),
            scheduled_time=scheduled_time,
        )

    @database_sync_to_async
    def serialize_messages(self, messages):
        return GroupMessageSerializer(
            messages, many=True, context={"user": self.user}
        ).data

    @database_sync_to_async
    def serialize_message(self, message):
        return GroupMessageSerializer(message).data

    @database_sync_to_async
    def get_group_members(self):
        """Retrieve members of the group."""
        group = self.group
        return [UserSerializer(user).data for user in group.members.all()]

    @database_sync_to_async
    def add_user_to_group(self):
        """Add user to group if not already added."""
        GroupParticipant.objects.get_or_create(group_id=self.group_id, user=self.user)

    @database_sync_to_async
    def remove_user_from_group(self):
        """Remove user from group."""
        GroupParticipant.objects.filter(group_id=self.group_id, user=self.user).delete()

    @database_sync_to_async
    def save_message(self, group: Group, user: User, data: dict):
        """Save a new group message."""
        valid_keys = {"text", "image", "file"}
        message_data = {key: data.get(key) for key in valid_keys if data.get(key)}

        return GroupMessage.objects.create(group=group, sender=user, **message_data)

    @database_sync_to_async
    def fetch_group_messages(self, pk: int):
        """Fetch messages for the group."""
        group = Group.objects.filter(pk=pk).first()
        if not group:
            return []
        return list(group.group_messages.order_by("sent_at"))

    @database_sync_to_async
    def update_user_status(self, is_online):
        """Update user's online status and last seen timestamp."""
        self.user.is_online = is_online
        self.user.update_last_seen()
        self.user.save()

    @database_sync_to_async
    def is_user_group_member(self):
        """Check if the user is a member of the group."""
        if self.group.owner.id == self.user.id:
            return True
        return self.group.members.filter(id=self.user.id).exists()

    async def is_authenticated(self):
        """Check if the user is authenticated."""
        return self.user.is_authenticated and not isinstance(self.user, AnonymousUser)

    async def has_group_access(self):
        """Check if the user has access to the group."""
        self.group = await self.get_group()
        if not self.group:
            return False

        if self.group.is_private:
            return await self.is_user_group_member()

        return True

    @database_sync_to_async
    def get_group_permission(self, group_id: int):
        return GroupPermission.objects.get(group_id=group_id)

    async def can_send_message(self, group_id: int):
        group_permission = await self.get_group_permission(group_id)

        return group_permission.can_send_messages
