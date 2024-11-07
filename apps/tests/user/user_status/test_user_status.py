import pytest
from rest_framework import status
from unittest.mock import MagicMock
from share.services import TokenService
from django.contrib.auth import get_user_model
from datetime import datetime, timezone

User = get_user_model()


@pytest.mark.django_db
def test_user_status_view_user_found(mocker, tokens, user_factory, api_client):
    """Test the UserStatusView returns correct data for a verified user."""
    last_seen_time = datetime(2024, 10, 28, 12, 0, tzinfo=timezone.utc)
    user = user_factory.create(
        is_verified=True, is_online=True, last_seen=last_seen_time
    )

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.get(f"/api/users/{user.id}/status/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["is_online"] is True
    assert response.data["last_seen"] == last_seen_time


@pytest.mark.django_db
def test_user_status_view_user_not_found(api_client):
    """Test the UserStatusView returns 404 if the user is not found or unverified."""
    client = api_client()

    response = client.get("/api/users/999/status/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
