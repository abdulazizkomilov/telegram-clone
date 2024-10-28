import pytest
from rest_framework import status
from unittest.mock import patch
from user.services import TokenService
from core import settings

LOGOUT_URL = "/api/users/logout/"


@pytest.mark.django_db
@patch.object(TokenService, 'add_token_to_redis')
def test_logout(mock_add_token, api_client, user_factory):
    user = user_factory.create()

    client = api_client()
    client.force_authenticate(user=user)

    response = client.post(LOGOUT_URL)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "Successfully logged out"}

    assert mock_add_token.call_count == 2
    mock_add_token.assert_any_call(
        user.id, 'fake_token', "access", settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
    )
    mock_add_token.assert_any_call(
        user.id, 'fake_token', "refresh", settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    )


@pytest.mark.django_db
def test_logout_unauthenticated(api_client):
    response = api_client().post(LOGOUT_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
