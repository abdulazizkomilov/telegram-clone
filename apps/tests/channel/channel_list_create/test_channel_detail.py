import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import MagicMock
from share.services import TokenService
from channel.models import Channel

User = get_user_model()


@pytest.mark.django_db
class TestChannelRetrieveUpdateDestroyView:
    @pytest.fixture
    def owner_user(self, user_factory):
        return user_factory.create()

    @pytest.fixture
    def member_user(self, user_factory):
        return user_factory.create()

    @pytest.fixture
    def channel(self, owner_user, member_user):
        channel = Channel.objects.create(name="Test Channel", owner=owner_user)
        channel.memberships.create(user=member_user)
        return channel

    def test_retrieve_channel_as_owner(
        self, mocker, api_client, tokens, owner_user, channel
    ):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(owner_user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.get(f"/api/channels/{channel.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(channel.id), "Channel ID mismatch in response"
        assert (
            response.data["owner"]["id"] == owner_user.id
        ), "Owner mismatch in response"

    def test_retrieve_channel_as_member(
        self, mocker, api_client, tokens, member_user, channel
    ):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(member_user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.get(f"/api/channels/{channel.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(channel.id), "Channel ID mismatch in response"

    def test_retrieve_channel_as_unauthorized(self, api_client, channel):
        client = api_client()

        response = client.get(f"/api/channels/{channel.id}/")
        assert (
            response.status_code == status.HTTP_401_UNAUTHORIZED
        ), "Expected unauthorized status code"

    def test_update_channel_as_owner(
        self, mocker, tokens, api_client, owner_user, channel
    ):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(owner_user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}
        data = {"name": "Updated Channel Name"}

        response = client.patch(f"/api/channels/{channel.id}/", data=data)
        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["name"] == "Updated Channel Name"
        ), "Channel name was not updated"

    def test_update_channel_as_member(
        self, mocker, tokens, api_client, member_user, channel
    ):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(member_user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        data = {"name": "Unauthorized Update"}

        response = client.patch(f"/api/channels/{channel.id}/", data=data)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), "Expected forbidden status code for non-owner"

    def test_update_channel_as_unauthorized(self, api_client, channel):
        client = api_client()
        data = {"name": "Unauthorized Update"}

        response = client.patch(f"/api/channels/{channel.id}/", data=data)
        assert (
            response.status_code == status.HTTP_401_UNAUTHORIZED
        ), "Expected unauthorized status code"

    def test_delete_channel_as_owner(
        self, mocker, tokens, api_client, owner_user, channel
    ):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(owner_user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.delete(f"/api/channels/{channel.id}/")
        assert (
            response.status_code == status.HTTP_204_NO_CONTENT
        ), "Expected no content status code for successful delete"
        assert not Channel.objects.filter(
            id=channel.id
        ).exists(), "Channel was not deleted"

    def test_delete_channel_as_member(
        self, mocker, tokens, api_client, member_user, channel
    ):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(member_user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.delete(f"/api/channels/{channel.id}/")
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), "Expected forbidden status code for non-owner"

    def test_delete_channel_as_unauthorized(self, api_client, channel):
        client = api_client()

        response = client.delete(f"/api/channels/{channel.id}/")
        assert (
            response.status_code == status.HTTP_401_UNAUTHORIZED
        ), "Expected unauthorized status code"
