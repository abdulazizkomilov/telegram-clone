import pytest
from django.conf import settings

MODEL_NAME = "Chat"
APP_NAME = "chat"
EXPECTED_DB_TABLE = "chat"
EXPECTED_VERBOSE_NAME = "Chat"
EXPECTED_VERBOSE_NAME_PLURAL = "Chats"
EXPECTED_ORDERING = ["-created_at"]


@pytest.mark.order(1)
@pytest.mark.django_db
def test_chat_app_exists():
    try:
        import chat  # noqa
    except ImportError:
        assert False, f"{APP_NAME} app folder missing"

    assert APP_NAME in settings.INSTALLED_APPS, f"{APP_NAME} app not installed"


@pytest.mark.order(2)
@pytest.mark.django_db
def test_custom_chat_model():
    """Test the custom chat model and its fields."""

    from chat.models import Chat

    assert Chat is not None, f"{MODEL_NAME} model not found"


@pytest.mark.order(3)
@pytest.mark.django_db
def test_chat_model(chat_factory):
    """Test the custom chat model and its fields."""
    chat = chat_factory()
    assert chat.id is not None
    assert chat is not None, f"{MODEL_NAME} model not found"
