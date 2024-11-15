from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer.generics import action
from django.contrib.auth.models import AnonymousUser

from .models import (
    Group,
    GroupParticipant,
)
from .serializers import GroupMessageSerializer
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

    @action()
    async def get_messages(self, pk, **kwargs):
        messages = await self.fetch_group_messages(pk)
        serialized_messages = await self.serialize_messages(messages)

        await self.send_json(
            {"action": "get_messages", "messages": serialized_messages}
        )

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

    @database_sync_to_async
    def get_group(self):
        """Retrieve group by ID."""
        return Group.objects.filter(pk=self.group_id).first()

    @database_sync_to_async
    def serialize_messages(self, messages):
        return GroupMessageSerializer(
            messages, many=True, context={"user": self.user}
        ).data

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
