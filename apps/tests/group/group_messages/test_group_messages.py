import pytest
from rest_framework import status

from group.models import GroupMessage, GroupPermission
from django.contrib.auth import get_user_model
from unittest.mock import MagicMock
from share.services import TokenService

User = get_user_model()


@pytest.mark.django_db
class TestGroupMessageCreateView:
    @pytest.fixture
    def setup(
        self,
        mocker,
        api_client,
        tokens,
        user_factory,
        group_factory,
        generate_test_image,
        generate_test_file,
    ):
        self.user = user_factory.create()
        self.group = group_factory.create()

        self.group_permission = GroupPermission.objects.create(
            group=self.group, can_send_media=True
        )

        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(self.user)
        self.client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        self.image = generate_test_image
        self.test_file = generate_test_file

    def test_create_group_message_with_media(self, setup):
        """Test that an authenticated user can create a group message with a media file."""

        data = {"text": "Hello, group!", "image": self.image, "file": self.test_file}

        response = self.client.post(
            f"/api/groups/{self.group.id}/messages/", data, format="multipart"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert GroupMessage.objects.count() == 1

        message = response.data

        assert message["text"] == "Hello, group!"
        assert message["sender"]["id"] == self.user.id
        assert message["group"]["id"] == self.group.id
        assert message["image"] is not None
        assert message["file"] is not None

    def test_create_group_message_without_permission(self, setup):
        """Test that a user cannot create a group message without permission."""
        self.group_permission.can_send_media = False
        self.group_permission.save()

        data = {"text": "Hello, group!", "image": self.image, "file": self.test_file}

        response = self.client.post(
            f"/api/groups/{self.group.id}/messages/", data, format="multipart"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert GroupMessage.objects.count() == 0

    def test_create_group_message_unauthenticated(self, setup):
        """Test that an unauthenticated user cannot create a group message."""
        self.client.force_authenticate(user=None)

        data = {"text": "Hello, group!"}

        response = self.client.post(
            f"/api/groups/{self.group.id}/messages/", data, format="multipart"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert GroupMessage.objects.count() == 0
