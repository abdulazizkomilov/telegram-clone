import pytest
from channels.testing import WebsocketCommunicator
from core.asgi import application
from user.models import User
from chat.models import Chat
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer


@database_sync_to_async
def create_user(phone_number):
    return User.objects.create(
        phone_number=phone_number, is_verified=True, is_active=True
    )


@database_sync_to_async
def create_chat(owner, user):
    return Chat.objects.create(owner=owner, user=user)


@pytest.fixture
def channel_layer(settings):
    """Override the channel layer to use an in-memory channel layer for testing."""
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
    return get_channel_layer()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_chat_consumer(tokens, channel_layer):
    user1 = await create_user("+998987654321")
    user2 = await create_user("+998987654322")
    chat = await create_chat(user1, user2)

    access, _ = tokens(user1)

    communicator = WebsocketCommunicator(
        application, f"/ws/chats/{chat.id}/?token={access}"
    )

    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await communicator.disconnect()
