import pytest
import jwt
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from core import settings
from core.asgi import application
from channels.layers import get_channel_layer

User = get_user_model()


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
class TestChatConsumer:
    @database_sync_to_async
    def create_user(self, user_factory):
        """Create a user using the provided user factory."""
        return user_factory.create()

    @database_sync_to_async
    def create_chat(self, chat_factory, owner, user):
        """Create a chat using the provided chat factory."""
        return chat_factory.create(owner=owner, user=user)

    @pytest.fixture
    async def chat(self, user_factory, chat_factory):
        """Fixture to create a chat instance with participants."""
        owner = await self.create_user(user_factory)
        participant = await self.create_user(user_factory)
        chat_instance = await self.create_chat(chat_factory, owner, participant)
        return chat_instance, owner, participant

    async def generate_token_payload(self, owner_id):
        """Generate a JWT payload for the user."""
        return {
            "user_id": str(owner_id),
            "exp": datetime.utcnow() + timedelta(minutes=10),
        }

    def generate_jwt_token(self, payload):
        """Generate a JWT token from the payload."""
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    @pytest.mark.asyncio
    @patch("redis.asyncio.client.Redis")
    @patch("share.middleware.jwt.decode")
    async def test_chat_message_like(
        self, mock_jwt_decode, mock_redis, chat, channel_layer
    ):
        """This test checks that the chat messaging system works correctly."""
        mock_connection = AsyncMock()
        mock_redis.return_value = mock_connection

        chat_instance, owner, _ = await chat

        token_payload = await self.generate_token_payload(owner.id)
        mock_jwt_decode.return_value = token_payload

        token = self.generate_jwt_token(token_payload)
        communicator = WebsocketCommunicator(
            application, f"/ws/chats/{chat_instance.pk}/?token={token}"
        )

        connected, _ = await communicator.connect()
        assert connected, "WebSocket connection failed with a valid token."

        messages = await communicator.receive_json_from()
        assert messages["action"] == "get_messages", "Expected get_messages action"
        assert len(messages["messages"]) == 0, "Expected no messages"

        users = await communicator.receive_json_from()
        assert users["users"][0]["id"] == str(owner.id), "Expected user ID"

        json_message_data = {
            "action": "create_message",
            "request_id": "1",
            "pk": str(chat_instance.pk),
            "data": {"text": "Hello, group!"},
        }

        await communicator.send_json_to(json_message_data)

        new_message_data = await communicator.receive_json_from()
        assert (
            new_message_data["action"] == "new_message"
        ), "Expected new_message action"
        assert (
            new_message_data["data"]["text"] == "Hello, group!"
        ), "Expected 'Hello, group!' message"
        assert new_message_data["data"]["chat"]["id"] == str(
            chat_instance.pk
        ), "Expected chat ID"

        like_data = {
            "action": "like_message",
            "request_id": "2",
            "pk": str(chat_instance.pk),
            "message_id": new_message_data["data"]["id"],
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
            liked_message_data["data"]["id"] == new_message_data["data"]["id"]
        ), "Expected message ID"
        assert liked_message_data["data"]["likes_count"] == 1, "Expected 1 like"

        remove_like_data = {
            "action": "unlike_message",
            "request_id": "2",
            "pk": str(chat_instance.pk),
            "message_id": new_message_data["data"]["id"],
        }

        await communicator.send_json_to(remove_like_data)
        await asyncio.sleep(0.2)

        removed_message_data = await communicator.receive_json_from()
        assert (
            removed_message_data["action"] == "message_unliked"
        ), "Expected message_unliked action"
        assert (
            removed_message_data["data"]["id"] == new_message_data["data"]["id"]
        ), "Expected message ID"
        assert len(removed_message_data["data"]["liked_by"]) == 0, "Expected 0"
        assert removed_message_data["data"]["likes_count"] == 0, "Expected 0 likes"

        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_invalid_chat_id(self, chat, channel_layer):
        """Test that connection fails with an invalid token."""
        invalid_token = "invalid.token.value"
        chat_instance, _, _ = await chat

        communicator = WebsocketCommunicator(
            application,
            f"/ws/chats/389ac0dc-bf6f-443f-af90-0cff66cff642/?token={invalid_token}",
        )

        connected, _ = await communicator.connect()
        assert not connected, "Connection should not succeed with an invalid token."

        await communicator.disconnect()
