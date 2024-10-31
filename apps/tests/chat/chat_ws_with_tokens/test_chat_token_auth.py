import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from chat.consumers import ChatConsumer
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.urls import path
from share.middleware import JwtAuthMiddlewareStack
from channels.layers import get_channel_layer

User = get_user_model()

application = ProtocolTypeRouter({
    "websocket": JwtAuthMiddlewareStack(
        URLRouter([
            path("ws/chat/<str:pk>/", ChatConsumer.as_asgi()),
        ])
    ),
})


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
    @patch('redis.asyncio.client.Redis')
    @patch("share.middleware.jwt.decode")
    async def test_valid_token_and_chat_connection(self, mock_jwt_decode, mock_redis, chat, channel_layer):
        """Test successful connection with a valid token and chat ID."""
        mock_connection = AsyncMock()
        mock_redis.return_value = mock_connection

        chat_instance, owner, _ = await chat

        token_payload = await self.generate_token_payload(owner.id)
        mock_jwt_decode.return_value = token_payload

        token = self.generate_jwt_token(token_payload)
        communicator = WebsocketCommunicator(application, f"/ws/chat/{chat_instance.pk}/?token={token}")

        connected, _ = await communicator.connect()
        assert connected, "WebSocket connection failed with a valid token."

        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_invalid_token(self, chat, channel_layer):
        """Test that connection fails with an invalid token."""
        invalid_token = "invalid.token.value"
        chat_instance, _, _ = await chat

        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{chat_instance.pk}/?token={invalid_token}",
        )

        connected, _ = await communicator.connect()
        assert not connected, "Connection should not succeed with an invalid token."

        await communicator.disconnect()
