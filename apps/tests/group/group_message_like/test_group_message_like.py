import pytest
import jwt
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from group.consumers import GroupConsumer
from group.models import GroupPermission
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.urls import path
from share.middleware import JwtAuthMiddlewareStack
from channels.layers import get_channel_layer

User = get_user_model()

application = ProtocolTypeRouter(
    {
        "websocket": JwtAuthMiddlewareStack(
            URLRouter(
                [
                    path("ws/groups/<str:pk>/", GroupConsumer.as_asgi()),
                ]
            )
        ),
    }
)


@pytest.fixture
def channel_layer(settings):
    """Override the channel layer to use an in-memory channel layer for testing."""
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
    return get_channel_layer()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGroupConsumer:
    @database_sync_to_async
    def create_user(self, user_factory):
        """Create a user using the provided user factory."""
        return user_factory.create()

    @database_sync_to_async
    def create_group(self, group_factory, owner, is_private=False):
        """Create a group using the provided group factory."""
        return group_factory.create(owner=owner, is_private=is_private)

    @database_sync_to_async
    def create_group_premission(self, group):
        """Create a group permission using the provided group factory."""
        return GroupPermission.objects.create(group=group)

    @pytest.fixture
    async def group(self, user_factory, group_factory):
        """Fixture to create a group instance with participants."""
        owner = await self.create_user(user_factory)
        member = await self.create_user(user_factory)
        group_instance = await self.create_group(group_factory, owner)
        await self.create_group_premission(group_instance)
        return group_instance, owner, member

    async def generate_token_payload(self, user_id):
        """Generate a JWT payload for the user."""
        return {
            "user_id": str(user_id),
            "exp": datetime.utcnow() + timedelta(minutes=10),
        }

    def generate_jwt_token(self, payload):
        """Generate a JWT token from the payload."""
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    @pytest.mark.asyncio
    @patch("redis.asyncio.client.Redis")
    @patch("share.middleware.jwt.decode")
    async def test_chat_connection(
        self, mock_jwt_decode, mock_redis, group, channel_layer
    ):
        """Test WebSocket connection based on user scenario."""
        mock_connection = AsyncMock()
        mock_redis.return_value = mock_connection

        group_instance, owner, _ = await group

        token_payload = await self.generate_token_payload(owner.id)
        mock_jwt_decode.return_value = token_payload

        token = self.generate_jwt_token(token_payload)
        communicator = WebsocketCommunicator(
            application, f"/ws/groups/{group_instance.pk}/?token={token}"
        )

        connected, _ = await communicator.connect()
        assert connected, "Connection should succeed with valid token."

        messages = await communicator.receive_json_from()
        assert messages["action"] == "get_messages"
        assert len(messages["messages"]) == 0
        await communicator.receive_json_from()

        json_data = {
            "action": "create_message",
            "request_id": "1",
            "pk": str(group_instance.pk),
            "data": {"text": "Hello, group!"},
        }
        await communicator.send_json_to(json_data)
        await asyncio.sleep(0.2)
        data = await communicator.receive_json_from()

        like_data = {
            "action": "like_message",
            "request_id": "2",
            "pk": str(group_instance.pk),
            "message_id": data["data"]["id"],
        }

        await communicator.send_json_to(like_data)
        await asyncio.sleep(0.2)

        liked_message_data = await communicator.receive_json_from()
        assert (
            liked_message_data["action"] == "message_liked"
        ), "Expected message_liked action"
        assert liked_message_data["data"]["liked_by"][0]["id"] == str(
            owner.id
        ), "Expected liked_by ID"
        assert (
            liked_message_data["data"]["id"] == data["data"]["id"]
        ), "Expected message ID"
        assert liked_message_data["data"]["likes_count"] == 1, "Expected 1 like"

        remove_like_data = {
            "action": "unlike_message",
            "request_id": "2",
            "pk": str(group_instance.pk),
            "message_id": data["data"]["id"],
        }

        await communicator.send_json_to(remove_like_data)
        await asyncio.sleep(0.2)

        removed_message_data = await communicator.receive_json_from()
        assert (
            removed_message_data["action"] == "message_unliked"
        ), "Expected message_unliked action"
        assert (
            removed_message_data["data"]["id"] == data["data"]["id"]
        ), "Expected message ID"
        assert len(removed_message_data["data"]["liked_by"]) == 0, "Expected 0"
        assert removed_message_data["data"]["likes_count"] == 0, "Expected 0 likes"

        await communicator.disconnect()
