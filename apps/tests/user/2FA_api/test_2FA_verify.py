import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
import hashlib

User = get_user_model()


@pytest.mark.order(3)
@pytest.mark.django_db
def test_verify_otp_2fa_enabled(api_client, user_factory, mocker):
    """Test verifying OTP with 2FA enabled and ensuring cache is set."""
    user = user_factory.create(phone_number="+998934563789", is_2fa_enabled=True)

    client = api_client()

    otp_secret = "valid-otp-secret"
    otp_code = "168467"

    redis_conn = mocker.Mock()
    mocker.patch("user.views.redis_conn", redis_conn)
    mocker.patch("share.utils.redis_conn", redis_conn)

    mocker.patch("user.serializers.check_otp", side_effect=None)

    mocker.patch(
        "user.views.UserService.create_tokens",
        return_value={"access": "fake-access-token", "refresh": "fake-refresh-token"},
    )

    response = client.patch(
        f"/api/users/verify/{otp_secret}/",
        data={"phone_number": user.phone_number, "otp_code": otp_code},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["detail"] == "2FA enabled, please verify your password"
    assert str(response.data["user_id"]) == user.id


@pytest.fixture
def verify_2fa_success_data(request, user_factory):
    """Fixture providing different data scenarios for 2FA verification."""
    user = user_factory.create()
    otp_secret = "valid-otp-secret"

    scenarios = {
        "valid_data": {
            "user_id": user.id,
            "password": otp_secret,
        },
        "invalid_password": {
            "user_id": user.id,
            "password": "invalid-password",
        },
        "invalid_user_data": {
            "user_id": 9999,
            "password": otp_secret,
        },
        "empty_user_id": {
            "user_id": "",
            "password": otp_secret,
        },
        "empty_password": {
            "user_id": user.id,
            "password": "",
        },
    }

    return scenarios[request.param]


@pytest.mark.order(4)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "verify_2fa_success_data",
    [
        "valid_data",
        "invalid_password",
        "invalid_user_data",
        "empty_user_id",
        "empty_password",
    ],
    indirect=True,
)
def test_verify_2fa(api_client, verify_2fa_success_data, user_factory, mocker):
    """Parameterized test for 2FA verification with various scenarios."""
    user = user_factory.create()
    client = api_client()

    otp_secret = "valid-otp-secret"
    hashed_secret = hashlib.sha1(otp_secret.encode("utf-8")).hexdigest()
    user.otp_secret = hashed_secret
    user.is_2fa_enabled = True
    user.save()

    redis_conn = mocker.Mock()
    mocker.patch("user.views.redis_conn", redis_conn)

    mock_create_tokens = mocker.patch(
        "user.views.UserService.create_tokens",
        return_value={"access": "fake-access-token", "refresh": "fake-refresh-token"},
    )

    response = client.post(
        "/api/users/2fa/verify/", verify_2fa_success_data, format="json"
    )

    if (
        verify_2fa_success_data["user_id"] == user.id
        and verify_2fa_success_data["password"] == otp_secret
    ):
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        mock_create_tokens.assert_called_once_with(user)
    else:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
