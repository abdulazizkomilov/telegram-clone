import pytest
from unittest.mock import MagicMock
from share.services import TokenService
from rest_framework import status
from chat.models import Chat, ChatParticipant


@pytest.fixture
def chat_data(chat_factory, user_factory):
    owner = user_factory.create(phone_number="+998934567890", username="+998934567890")
    user = user_factory.create(phone_number="+998934567891", username="+998934567891")
    chat_instance = chat_factory.create(owner=owner, user=user)
    ChatParticipant.objects.create(chat=chat_instance, user=owner)
    ChatParticipant.objects.create(chat=chat_instance, user=user)
    return chat_instance, owner, user


@pytest.mark.order(1)
@pytest.mark.django_db
class TestChatListCreateView:
    def test_list_chats(self, mocker, tokens, api_client, chat_data):
        """Test that the user can list their chats."""
        chat, owner, user = chat_data

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(owner)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.get("/api/chats/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == str(chat.id)

    def test_create_chat(self, mocker, tokens, api_client, user_factory):
        """Test that the user can create a chat."""
        owner = user_factory.create()
        user = user_factory.create()

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(owner)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        payload = {"owner_id": str(owner.id), "user_id": str(user.id)}
        response = client.post("/api/chats/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["owner"]["id"] == str(owner.id)
        assert response.data["user"]["id"] == str(user.id)

    def test_create_chat_already_exists(self, mocker, tokens, api_client, chat_data):
        """Test that the user can create a chat."""
        chat, owner, user = chat_data

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(owner)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        payload = {"owner_id": str(owner.id), "user_id": str(user.id)}
        response = client.post("/api/chats/", payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.order(2)
@pytest.mark.django_db
class TestChatView:
    @pytest.mark.parametrize(
        "auth_user, expected_status",
        [
            ("owner", status.HTTP_200_OK),
            ("non_owner", status.HTTP_404_NOT_FOUND),
        ],
    )
    def test_retrieve_chat(
        self,
        mocker,
        tokens,
        api_client,
        chat_data,
        user_factory,
        auth_user,
        expected_status,
    ):
        chat, owner, user = chat_data
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        if auth_user == "owner":
            access, _ = tokens(owner)
            client = api_client(access)
            mock_redis_client.smembers.return_value = {access.encode()}
        else:
            user_1 = user_factory.create()
            access, _ = tokens(user_1)
            client = api_client(access)
            mock_redis_client.smembers.return_value = {access.encode()}

        response = client.get(f"/api/chats/{chat.id}/")

        assert (
            response.status_code == expected_status
        ), f"Unexpected status code: {response.status_code}"
        if expected_status == status.HTTP_200_OK:
            assert response.data["id"] == str(chat.id), "Chat ID does not match"

    @pytest.mark.parametrize(
        "auth_user, expected_status",
        [
            ("owner", status.HTTP_204_NO_CONTENT),
            ("non_owner", status.HTTP_404_NOT_FOUND),
        ],
    )
    def test_delete_chat(
        self,
        mocker,
        tokens,
        api_client,
        chat_data,
        user_factory,
        auth_user,
        expected_status,
    ):
        """Test that the chat can be deleted by the owner or not deleted by a non-owner."""
        chat, owner, user = chat_data
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        if auth_user == "owner":
            access, _ = tokens(owner)
            client = api_client(access)
            mock_redis_client.smembers.return_value = {access.encode()}
            response = client.delete(f"/api/chats/{chat.id}/")
            assert response.status_code == expected_status
            assert (
                not Chat.objects.filter(id=chat.id).exists()
                if expected_status == status.HTTP_204_NO_CONTENT
                else True
            )
        else:
            user_1 = user_factory.create()
            access, _ = tokens(user_1)
            client = api_client(access)
            mock_redis_client.smembers.return_value = {access.encode()}
            response = client.delete(f"/api/chats/{chat.id}/")

            assert response.status_code == expected_status
