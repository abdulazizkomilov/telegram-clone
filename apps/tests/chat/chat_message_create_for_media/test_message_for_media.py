import pytest
from rest_framework import status
from unittest.mock import MagicMock
from share.services import TokenService
from channels.layers import get_channel_layer
from unittest.mock import patch, AsyncMock
from chat.models import Message


@pytest.mark.django_db
class TestMessageListCreateView:
    """Test that authenticated users can list and create messages."""

    @pytest.fixture
    def channel_layer(settings):
        """Override the channel layer to use an in-memory channel layer for testing."""
        settings.CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels.layers.InMemoryChannelLayer",
            },
        }
        return get_channel_layer()

    def test_list_messages(
        self, mocker, tokens, api_client, user_factory, chat_factory
    ):
        """Test that authenticated users can list messages."""
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        user = user_factory.create()
        owner = user_factory.create()
        chat = chat_factory.create(owner=owner, user=user)

        Message.objects.create(chat=chat, sender=owner, text="Hello!")

        access, _ = tokens(user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.get(f"/api/chats/{chat.id}/messages/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["text"] == "Hello!"

    def test_create_message(
        self,
        mocker,
        tokens,
        api_client,
        user_factory,
        chat_factory,
        channel_layer,
        generate_test_image,
        generate_test_file,
    ):
        """Test that a message is created and group_send is called."""
        user = user_factory.create()
        chat = chat_factory.create(owner=user, user=user)

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        test_image = generate_test_image
        test_file = generate_test_file

        payload = {
            "text": "Message with file and image",
            "file": test_file,
            "image": test_image,
        }

        with patch.object(
            channel_layer, "group_send", new_callable=AsyncMock
        ) as mock_group_send:
            response = client.post(
                f"/api/chats/{chat.id}/messages/", payload, format="multipart"
            )

            assert response.status_code == status.HTTP_201_CREATED
            message = Message.objects.get(text="Message with file and image")

            assert str(message.chat) == str(chat)
            assert str(message.sender) == str(user)
            assert message.file is not None
            assert message.image is not None

            mock_group_send.assert_called_once()

            called_args = mock_group_send.call_args[0][1]
            assert str(called_args["message_id"]) == str(message.id)

    def test_create_message_without_auth(self, api_client, user_factory, chat_factory):
        """Test that a message cannot be created without authentication."""

        user = user_factory.create()
        chat = chat_factory.create(owner=user, user=user)

        client = api_client()
        payload = {"text": "Unauthorized message"}

        response = client.post(
            f"/api/chats/{chat.id}/messages/", payload, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
