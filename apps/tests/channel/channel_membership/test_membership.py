import pytest
from rest_framework import status
from unittest.mock import MagicMock
from share.services import TokenService
from django.contrib.auth import get_user_model
from channel.models import Channel, ChannelMembership

User = get_user_model()


@pytest.mark.django_db
class TestChannelMembershipListCreateView:
    @pytest.fixture
    def channel(self, user_factory):
        owner = user_factory.create()
        return Channel.objects.create(
            name="Test Channel", owner=owner, channel_type="public"
        )

    @pytest.fixture
    def private_channel(self, user_factory):
        owner = user_factory.create()
        return Channel.objects.create(
            name="Private Channel", owner=owner, channel_type="private"
        )

    def test_list_memberships(self, mocker, tokens, api_client, channel, user_factory):
        member = user_factory.create()
        ChannelMembership.objects.create(channel=channel, user=member, role="member")

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(channel.owner)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.get(f"/api/channels/{channel.id}/memberships/")
        assert response.status_code == status.HTTP_200_OK
        assert (
            len(response.data["results"]) == 1
        ), "Expected one membership in the response"

    def test_create_membership_in_public_channel(
        self, mocker, tokens, api_client, channel, user_factory
    ):
        user = user_factory.create()
        data = {"user_id": str(user.id), "role": "member"}

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(channel.owner)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.post(f"/api/channels/{channel.id}/memberships/", data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["id"] == str(
            user.id
        ), "User ID mismatch in response"
        assert response.data["role"] == "member", "Role mismatch in response"

    def test_create_membership_in_private_channel_as_owner(
        self, mocker, tokens, api_client, private_channel, user_factory
    ):
        user = user_factory.create()
        data = {"user_id": str(user.id), "role": "member"}

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(private_channel.owner)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.post(
            f"/api/channels/{private_channel.id}/memberships/", data=data
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_membership_in_private_channel_as_non_admin(
        self, mocker, tokens, api_client, private_channel, user_factory
    ):
        user = user_factory.create()
        non_admin_user = user_factory.create()
        private_channel.memberships.create(user=non_admin_user, role="member")

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(non_admin_user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        data = {"user_id": str(user.id), "role": "member"}
        response = client.post(
            f"/api/channels/{private_channel.id}/memberships/", data=data
        )

        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), "Non-admin should not be allowed to add members to private channels"


@pytest.mark.django_db
class TestChannelMembershipUpdateDestroyView:
    @pytest.fixture
    def channel(self, user_factory):
        owner = user_factory.create()
        return Channel.objects.create(name="Test Channel", owner=owner)

    @pytest.fixture
    def membership(self, channel, user_factory):
        member = user_factory.create()
        return ChannelMembership.objects.create(
            channel=channel, user=member, role="member"
        )

    def test_update_membership_as_owner(
        self, mocker, tokens, api_client, channel, membership
    ):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(channel.owner)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        data = {"role": "admin"}

        response = client.patch(
            f"/api/channels/{channel.id}/memberships/{membership.id}/", data=data
        )
        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["role"] == "admin"
        ), "Role should be updated to 'admin' by the owner"

    def test_update_membership_as_non_owner(
        self, mocker, tokens, api_client, membership, user_factory
    ):
        non_owner_user = user_factory.create()

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(non_owner_user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        data = {"role": "admin"}

        response = client.patch(
            f"/api/channels/{membership.channel.id}/memberships/{membership.id}/",
            data=data,
        )
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), "Non-owner should not be able to update roles"

    def test_delete_membership_as_owner(
        self, mocker, tokens, api_client, channel, membership
    ):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(channel.owner)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.delete(
            f"/api/channels/{channel.id}/memberships/{membership.id}/"
        )
        assert (
            response.status_code == status.HTTP_204_NO_CONTENT
        ), "Owner should be able to delete a membership"
        assert not ChannelMembership.objects.filter(
            id=membership.id
        ).exists(), "Membership should be deleted"

    def test_delete_membership_as_non_owner(
        self, mocker, tokens, api_client, membership, user_factory
    ):
        non_owner_user = user_factory.create()

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(non_owner_user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.delete(
            f"/api/channels/{membership.channel.id}/memberships/{membership.id}/"
        )
        assert (
            response.status_code == status.HTTP_204_NO_CONTENT
        ), "Non-owner should be able to delete a membership"
