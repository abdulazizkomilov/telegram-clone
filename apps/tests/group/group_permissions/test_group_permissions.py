import pytest
from rest_framework import status
from group.models import Group, GroupPermission
from unittest.mock import MagicMock
from share.services import TokenService


@pytest.mark.django_db
class TestGroupPermissionSerializer:
    @pytest.mark.parametrize(
        "data, expected_status",
        [
            ({"can_send_messages": False, "can_send_media": True}, status.HTTP_200_OK),
            ({"can_send_messages": "invalid"}, status.HTTP_400_BAD_REQUEST),
            ({"can_send_media": None}, status.HTTP_400_BAD_REQUEST),
            (
                {"can_send_messages": None, "can_send_media": None},
                status.HTTP_400_BAD_REQUEST,
            ),
        ],
    )
    def test_group_permission_update(
        self, mocker, api_client, tokens, user_factory, data, expected_status
    ):
        user = user_factory()

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(user)
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        group_data = {"name": "New Group", "is_private": True}

        response = client.post("/api/groups/", group_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        group = Group.objects.get(id=response.data["id"])

        response = client.patch(
            f"/api/groups/{group.id}/permissions/", data, format="json"
        )

        assert response.status_code == expected_status

        if expected_status == status.HTTP_200_OK:
            group_permission = GroupPermission.objects.get(group=group)
            assert group_permission.can_send_messages is False
            assert group_permission.can_send_media is True
