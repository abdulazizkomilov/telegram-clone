import pytest
from rest_framework import status
from unittest.mock import MagicMock
from share.services import TokenService
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.order(1)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "data, expected_status, expected_detail",
    [
        (
            {"type": True, "otp_secret": "lkj98sKLl3f3lkd"},
            status.HTTP_200_OK,
            {"detail": "2FA enabled."},
        ),
        (
            {"type": True, "otp_secret": "lk"},
            status.HTTP_400_BAD_REQUEST,
            {"detail": "OTP secret must be at least 8 characters long."},
        ),
        (
            {"type": False, "otp_secret": ""},
            status.HTTP_200_OK,
            {"detail": "2FA disabled."},
        ),
    ],
)
def test_enable_2fa(
    mocker, tokens, api_client, user, data, expected_status, expected_detail
):
    """Test enabling and disabling 2FA for a user."""
    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.post("/api/users/2fa/", data, format="json")
    assert response.status_code == expected_status

    if expected_status == status.HTTP_400_BAD_REQUEST:
        assert response.data[0] == expected_detail["detail"]
    else:
        assert response.data == expected_detail

    if data["type"] and expected_status == status.HTTP_200_OK:
        user.refresh_from_db()
        assert user.is_2fa_enabled is True
        assert user.otp_secret is not None
    else:
        user.refresh_from_db()
        assert user.is_2fa_enabled is False


@pytest.mark.order(2)
@pytest.mark.django_db
def test_disable_2fa_success(mocker, tokens, api_client, user):
    """Test disabling 2FA for a user."""
    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    data = {"type": True, "otp_secret": "some-otp-secret"}
    client.post("/api/users/2fa/", data, format="json")

    data = {"type": False, "otp_secret": ""}

    response = client.post("/api/users/2fa/", data, format="json", user=user)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"detail": "2FA disabled."}
    user.refresh_from_db()
    assert user.is_2fa_enabled is False
    assert user.otp_secret is None
