import pytest
from rest_framework import status
from unittest.mock import MagicMock
from share.services import TokenService
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def private_group_data(user_factory, group_factory):
    owner = user_factory.create()
    group = group_factory.create(name="Private Group", owner=owner, is_private=True)
    return group, owner


@pytest.mark.django_db
class TestGroupAddMemberView:
    @pytest.fixture
    def setup(self, mocker, api_client, tokens, private_group_data):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        self.group, self.owner = private_group_data

        access, _ = tokens(self.owner)
        self.client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

    def test_add_member_to_private_group(self, setup, user_factory):
        """Test that the group owner can add members to a private group."""
        new_member = user_factory.create()
        response = self.client.patch(
            f"/api/groups/{self.group.id}/members/", {"members": [new_member.id]}
        )
        assert response.status_code == status.HTTP_200_OK

        self.group.refresh_from_db()

        assert self.group.members.filter(id=new_member.id).exists()

    def test_add_member_to_non_private_group(self, setup, group_factory):
        """Test that an error is raised when trying to add a member to a non-private group."""
        public_group = group_factory.create(
            name="Public Group", owner=self.owner, is_private=False
        )
        response = self.client.patch(
            f"/api/groups/{public_group.id}/members/", {"members": []}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_member_not_owner(self, setup, user_factory):
        """Test that a non-owner cannot add members to a private group."""
        non_owner = user_factory.create()
        self.client.force_authenticate(user=non_owner)
        response = self.client.patch(
            f"/api/groups/{self.group.id}/members/", {"members": []}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
