import pytest
from unittest.mock import MagicMock
from rest_framework import status
from share.services import TokenService
from core import settings


class MockUserIndex:
    @staticmethod
    def search():
        mock_search_instance = MagicMock()
        mock_search_instance.query.return_value.execute.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "phone_number": "12345",
                    "first_name": "John",
                    "last_name": "Doe",
                }
            )
        ]
        return mock_search_instance


class MockGroupIndex:
    @staticmethod
    def search():
        mock_search_instance = MagicMock()
        mock_search_instance.query.return_value.execute.return_value = [
            MagicMock(to_dict=lambda: {"name": "Django Group"})
        ]
        return mock_search_instance


class MockChannelIndex:
    @staticmethod
    def search():
        mock_search_instance = MagicMock()
        mock_search_instance.query.return_value.execute.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "name": "General Channel",
                    "description": "Channel for general discussions",
                }
            )
        ]
        return mock_search_instance


@pytest.mark.django_db
def test_search_view(api_client, mocker, tokens, user_factory):
    mocker.patch.object(settings, "ENABLE_ES", True)

    mocker.patch("share.views.UserIndex", new=MockUserIndex)
    mocker.patch("share.views.GroupIndex", new=MockGroupIndex)
    mocker.patch("share.views.ChannelIndex", new=MockChannelIndex)

    search_query = "John"
    user = user_factory.create()

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )
    access, _ = tokens(user)
    client = api_client(access)
    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.get(f"/api/search/{search_query}/")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    expected_data = {
        "users": [{"phone_number": "12345", "first_name": "John", "last_name": "Doe"}],
        "groups": [{"name": "Django Group"}],
        "channels": [
            {
                "name": "General Channel",
                "description": "Channel for general discussions",
            }
        ],
    }

    assert response_data == expected_data


@pytest.mark.django_db
def test_search_view_unauthorized(api_client):
    client = api_client()

    response = client.get("/api/search/john/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
