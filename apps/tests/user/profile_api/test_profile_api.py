import pytest
from unittest.mock import MagicMock
from share.services import TokenService
from rest_framework import status

PROFILE_URL = "/api/users/profile/"


@pytest.fixture
def user_profile_data(user_factory):
    """Create a test user with is_verified=True."""
    return user_factory.create(
        user_name="developer",
        bio="This is a bio",
        birth_date="1995-05-10",
        first_name="John",
        last_name="Doe",
        is_verified=True,
        is_active=True,
    )


@pytest.fixture
def unverified_user_data(user_factory):
    """Create a test user with is_verified=False."""
    return user_factory.create(
        user_name="unverified_user",
        bio="Unverified user bio",
        birth_date="2000-01-01",
        first_name="Unverified",
        last_name="User",
        is_verified=False,
        is_active=True,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_fixture, expected_status, expected_response_keys",
    [
        (
            "user_profile_data",
            status.HTTP_200_OK,
            ["user_name", "bio", "first_name", "last_name"],
        ),
        ("unverified_user_data", status.HTTP_403_FORBIDDEN, None),
    ],
)
def test_user_profile_retrieve(
    mocker,
    tokens,
    api_client,
    request,
    user_fixture,
    expected_status,
    expected_response_keys,
):
    """Test retrieving profile for both verified and unverified users."""
    user = request.getfixturevalue(user_fixture)

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.get(PROFILE_URL)
    assert response.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        data = response.json()
        for key in expected_response_keys:
            assert key in data
            assert data[key] == getattr(user, key)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "update_data, expected_status, expected_error",
    [
        (
            {
                "user_name": "updateduser",
                "bio": "Updated bio",
                "first_name": "UpdatedFirstName",
                "last_name": "UpdatedLastName",
            },
            status.HTTP_200_OK,
            None,
        ),
        (
            {
                "bio": "Updated bio",
                "first_name": "UpdatedFirstName",
                "last_name": "UpdatedLastName",
            },
            status.HTTP_200_OK,
            None,
        ),
        (
            {"user_name": ""},
            status.HTTP_400_BAD_REQUEST,
            {"user_name": ["User name cannot be empty."]},
        ),
    ],
)
def test_user_profile_update(
    mocker,
    tokens,
    api_client,
    user_profile_data,
    update_data,
    expected_status,
    expected_error,
):
    """Test updating profile data."""
    user = user_profile_data

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.patch(PROFILE_URL, data=update_data, format="json")
    assert response.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        updated_user = response.json()
        for key, value in update_data.items():
            assert updated_user[key] == value
    elif expected_status == status.HTTP_400_BAD_REQUEST:
        assert response.data == expected_error


@pytest.mark.django_db
@pytest.mark.parametrize(
    "authenticated, expected_status",
    [
        (False, status.HTTP_401_UNAUTHORIZED),
        (True, status.HTTP_200_OK),
    ],
)
def test_user_profile_authentication(
    api_client, authenticated, expected_status, user_profile_data
):
    """Test access to profile based on authentication status."""
    client = api_client()

    if authenticated:
        client.force_authenticate(user=user_profile_data)

    response = client.get(PROFILE_URL)
    assert response.status_code == expected_status
