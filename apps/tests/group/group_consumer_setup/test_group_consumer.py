import pytest
from group.consumers import GroupConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer


@pytest.mark.order(1)
@pytest.mark.django_db
def test_group_consumer_exists():
    """Test that the GroupConsumer class is defined."""
    assert GroupConsumer is not None, "GroupConsumer class is missing."


@pytest.mark.order(2)
@pytest.mark.django_db
def test_group_consumer_inheritance():
    """Check that GroupConsumer inherits from required classes."""
    assert issubclass(
        GroupConsumer, AsyncJsonWebsocketConsumer
    ), "GroupConsumer must inherit from AsyncJsonWebsocketConsumer."


@pytest.mark.order(3)
@pytest.mark.django_db
def test_group_consumer_functions_exist():
    """Ensure connect and disconnect functions are implemented in GroupConsumer."""
    assert hasattr(
        GroupConsumer, "connect"
    ), "GroupConsumer is missing the 'connect' method."
    assert hasattr(
        GroupConsumer, "disconnect"
    ), "GroupConsumer is missing the 'disconnect' method."
