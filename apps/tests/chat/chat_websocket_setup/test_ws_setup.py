import pytest
from chat.consumers import ChatConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer


@pytest.mark.order(1)
@pytest.mark.django_db
def test_chat_consumer_exists():
    """Test that the ChatConsumer class is defined."""
    assert ChatConsumer is not None, "ChatConsumer class is missing."


@pytest.mark.order(2)
@pytest.mark.django_db
def test_chat_consumer_inheritance():
    """Check that ChatConsumer inherits from required classes."""
    assert issubclass(
        ChatConsumer, AsyncJsonWebsocketConsumer
    ), "ChatConsumer must inherit from AsyncJsonWebsocketConsumer."


@pytest.mark.order(3)
@pytest.mark.django_db
def test_chat_consumer_functions_exist():
    """Ensure connect and disconnect functions are implemented in ChatConsumer."""
    assert hasattr(
        ChatConsumer, "connect"
    ), "ChatConsumer is missing the 'connect' method."
    assert hasattr(
        ChatConsumer, "disconnect"
    ), "ChatConsumer is missing the 'disconnect' method."
