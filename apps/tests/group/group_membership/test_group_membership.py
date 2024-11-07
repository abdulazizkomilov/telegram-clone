import pytest
from rest_framework import status
from unittest.mock import MagicMock
from share.services import TokenService
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def group_data(user_factory, group_factory):
    owner = user_factory.create()
    group = group_factory.create(name="Test Group", owner=owner, is_private=False)
    group.members.add(owner)
    return group, owner


@pytest.fixture
def private_group_data(user_factory, group_factory):
    owner = user_factory.create()
    group = group_factory.create(name="Private Group", owner=owner, is_private=True)
    return group, owner


@pytest.mark.django_db
class TestJoinLeaveGroupView:
    @pytest.fixture
    def setup(self, mocker, api_client, tokens, user_factory, group_data):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        self.user = user_factory.create()
        self.group, self.owner = group_data

        access, _ = tokens(self.user)
        self.client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

    def test_join_group(self, setup):
        """Test that a user can join a public group."""
        response = self.client.post(f"/api/groups/{self.group.id}/memberships/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "You have successfully joined the group."

        self.group.refresh_from_db()

        assert self.group.members.filter(id=self.user.id).exists()

    def test_join_private_group(self, setup, private_group_data):
        """Test that a user cannot join a private group."""
        group, owner = private_group_data
        response = self.client.post(f"/api/groups/{group.id}/memberships/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "This group is private."

    def test_join_already_member(self, setup):
        """Test that a user cannot join a group they are already a member of."""
        self.group.members.add(self.user)
        response = self.client.post(f"/api/groups/{self.group.id}/memberships/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "You are already a member of this group."

    def test_leave_group(self, setup):
        """Test that a user can leave a group they are a member of."""
        self.group.members.add(self.user)
        response = self.client.delete(f"/api/groups/{self.group.id}/memberships/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "You have successfully left the group."

        self.group.refresh_from_db()

        assert self.user not in self.group.members.all()

    def test_leave_group_not_member(self, setup):
        """Test that a user cannot leave a group they are not a member of."""
        response = self.client.delete(f"/api/groups/{self.group.id}/memberships/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "You are not a member of this group."
