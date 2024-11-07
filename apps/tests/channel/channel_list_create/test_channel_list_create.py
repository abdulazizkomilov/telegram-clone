import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from channel.models import Channel

User = get_user_model()


@pytest.mark.django_db
class TestChannelListCreateView:
    @pytest.fixture
    def channel_owner(self, user_factory):
        return user_factory.create()

    @pytest.fixture
    def channel(self, channel_owner):
        return Channel.objects.create(name="Test Channel", owner=channel_owner)

    def test_get_channels_as_member_or_owner(self, api_client, user_factory, channel):
        user = user_factory.create()
        channel.memberships.create(user=user)

        client = api_client()
        client.force_authenticate(user=user)

        response = client.get("/api/channels/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert str(channel.id) in str(
            response.data["results"][0]["id"]
        ), "Channel ID not found in response"

    @pytest.mark.parametrize(
        "data, is_authenticated, expected_status, expected_channel_created",
        [
            (
                {
                    "name": "New Channel",
                    "description": "Test Channel",
                    "channel_type": "public",
                },
                True,
                status.HTTP_201_CREATED,
                True,
            ),
            (
                {"name": "New Channel", "description": "Test Channel"},
                True,
                status.HTTP_201_CREATED,
                True,
            ),
            ({"name": "New Channel"}, True, status.HTTP_201_CREATED, True),
            ({}, True, status.HTTP_400_BAD_REQUEST, False),
            ({}, False, status.HTTP_401_UNAUTHORIZED, False),
        ],
    )
    def test_create_channel(
        self,
        api_client,
        user_factory,
        data,
        is_authenticated,
        expected_status,
        expected_channel_created,
    ):
        user = user_factory.create()
        client = api_client()
        if is_authenticated:
            client.force_authenticate(user=user)

        response = client.post("/api/channels/", data=data)
        assert response.status_code == expected_status

        if expected_channel_created:
            assert response.data["name"] == "New Channel"
            created_channel = Channel.objects.get(name="New Channel")
            assert (
                created_channel.owner.username == user.username
            ), "The channel owner should be set to the authenticated user."
        else:
            assert Channel.objects.filter(name="New Channel").count() == 0
