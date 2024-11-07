import pytest
from unittest.mock import MagicMock
from rest_framework import status
from django.contrib.auth import get_user_model
from group.models import Group, GroupPermission
from share.services import TokenService

User = get_user_model()


@pytest.mark.django_db
class TestGroupAPI:
    @pytest.fixture
    def setup_group(self, mocker, api_client, tokens, user_factory, group_factory):
        user = user_factory()
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(user)
        client = api_client(access)
        mock_redis_client.smembers.return_value = {access.encode()}

        return client, user, group_factory

    def test_list_groups(self, setup_group):
        client, user, group_factory = setup_group
        group = group_factory(owner=user)
        group.members.add(user)
        group.save()

        response = client.get("/api/groups/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert group.name == response.data["results"][0]["name"]
        assert user.first_name == response.data["results"][0]["owner"]["first_name"]

    def test_create_group(self, setup_group):
        client, user, _ = setup_group

        group_data = {"name": "New Group", "is_private": True}

        response = client.post("/api/groups/", group_data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        new_group = Group.objects.get(name="New Group")
        assert new_group.owner.first_name == user.first_name
        assert new_group.is_private is True

        group_permission = GroupPermission.objects.filter(group=new_group).exists()
        assert group_permission

    @pytest.mark.parametrize(
        "owner_type, expected_status",
        [("owner", status.HTTP_200_OK), ("non_owner", status.HTTP_404_NOT_FOUND)],
    )
    def test_retrieve_group(
        self,
        mocker,
        api_client,
        tokens,
        user_factory,
        group_factory,
        owner_type,
        expected_status,
    ):
        owner = user_factory()
        member = user_factory()
        group = group_factory(name="Test Group", owner=owner)
        group.members.add(member)

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        if owner_type == "owner":
            access, _ = tokens(owner)
        else:
            non_owner = user_factory()
            access, _ = tokens(non_owner)

        client = api_client(access)
        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.get(f"/api/groups/{group.id}/")

        assert response.status_code == expected_status
        if expected_status == status.HTTP_200_OK:
            assert response.data["name"] == "Test Group"

    @pytest.mark.parametrize(
        "is_owner, expected_status",
        [(True, status.HTTP_204_NO_CONTENT), (False, status.HTTP_403_FORBIDDEN)],
    )
    def test_delete_group(
        self,
        mocker,
        api_client,
        tokens,
        user_factory,
        group_factory,
        is_owner,
        expected_status,
    ):
        owner = user_factory()
        non_owner = user_factory()
        group = group_factory(name="Test Group", owner=owner)

        if not is_owner:
            group.members.add(non_owner)

        access = tokens(owner if is_owner else non_owner)[0]
        client = api_client(access)

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )
        mock_redis_client.smembers.return_value = {access.encode()}

        response = client.delete(f"/api/groups/{group.id}/")

        assert response.status_code == expected_status
        assert (
            (not Group.objects.filter(id=group.id).exists())
            if is_owner
            else Group.objects.filter(id=group.id).exists()
        )
