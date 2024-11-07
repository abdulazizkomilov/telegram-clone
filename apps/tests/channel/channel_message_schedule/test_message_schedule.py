import pytest
from rest_framework import status
from django.utils import timezone
from unittest.mock import MagicMock
from share.services import TokenService
from channel.models import Channel, ChannelScheduledMessage


@pytest.mark.django_db
class TestCreateScheduledMessageView:
    @pytest.fixture
    def setup_data(self, user_factory):
        owner = user_factory.create()
        other_user = user_factory.create()
        channel = Channel.objects.create(name="Test Channel", owner=owner)
        return {"owner": owner, "other_user": other_user, "channel": channel}

    def test_successful_message_scheduling(
        self, setup_data, api_client, tokens, mocker
    ):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(setup_data["owner"])
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}

        data = {
            "text": "Scheduled message",
            "scheduled_time": (
                timezone.now() + timezone.timedelta(minutes=10)
            ).isoformat(),
        }

        response = client.post(
            f"/api/channels/{setup_data['channel'].id}/messages/schedule/",
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert ChannelScheduledMessage.objects.filter(
            channel=setup_data["channel"]
        ).exists()

    def test_channel_not_found(self, setup_data, mocker, api_client, tokens):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(setup_data["owner"])
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}
        data = {
            "text": "Message for non-existent channel",
            "scheduled_time": (
                timezone.now() + timezone.timedelta(minutes=10)
            ).isoformat(),
        }

        response = client.post(
            "/api/channels/1/messages/schedule/", data, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_scheduled_time_in_the_past(self, setup_data, mocker, api_client, tokens):
        mock_redis_client = MagicMock()
        mocker.patch.object(
            TokenService, "get_redis_client", return_value=mock_redis_client
        )

        access, _ = tokens(setup_data["owner"])
        client = api_client(access)

        mock_redis_client.smembers.return_value = {access.encode()}
        data = {
            "text": "Past message",
            "scheduled_time": (
                timezone.now() - timezone.timedelta(minutes=10)
            ).isoformat(),
        }

        response = client.post(
            f"/api/channels/{setup_data['channel'].id}/messages/schedule/",
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
