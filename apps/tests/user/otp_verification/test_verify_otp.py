import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()


@pytest.fixture
def verify_otp_data(request, fake_number, user_factory):
    otp_code = "168467"
    phone_number = fake_number
    otp_secret = "1v8z0Of5sJ0XI3cpNcHWrofrHZfY0oGJZbvGW4siTs0"
    return_data = {
        "status_code": 200,
        "check_otp_exception": None,
        "otp_secret": otp_secret,
        "phone_number": phone_number,
        "otp_code": otp_code,
        "req_json": {
            "phone_number": phone_number,
            "otp_code": otp_code,
        },
    }

    def valid_data():
        user_factory.create(phone_number=phone_number, is_verified=False)
        return return_data

    def invalid_after_expiration_time():
        user_factory.create(phone_number=phone_number, is_verified=False)
        return_data.update(
            {
                "status_code": 400,
                "check_otp_exception": ValidationError("Invalid OTP code.", 400),
            }
        )
        return return_data

    def invalid_phone_number():
        return_data.update({"status_code": 400})
        return_data["req_json"].update({"phone_number": "invalid_phone_number"})
        return return_data

    def empty_phone_number():
        return_data.update({"status_code": 400})
        return_data["req_json"].update({"phone_number": ""})
        return return_data

    def required_phone_number():
        return_data.update({"status_code": 400})
        return_data["req_json"].pop("phone_number")
        return return_data

    def incorrect_otp_code():
        user_factory.create(phone_number=phone_number, is_verified=False)
        return_data.update(
            {
                "status_code": 400,
                "check_otp_exception": ValidationError("Invalid OTP code.", 400),
            }
        )
        return_data["req_json"].update({"otp_code": "123456"})
        return return_data

    def invalid_otp_code():
        return_data.update({"status_code": 400})
        return_data["req_json"].update({"otp_code": "invalid_code"})
        return return_data

    def empty_otp_code():
        return_data.update({"status_code": 400})
        return_data["req_json"].update({"otp_code": ""})
        return return_data

    def required_otp_code():
        return_data.update({"status_code": 400})
        return_data["req_json"].pop("otp_code")
        return return_data

    def invalid_otp_secret():
        return_data.update(
            {
                "status_code": 400,
                "otp_secret": "invalid_otp_secret",
                "check_otp_exception": ValidationError("Invalid OTP code.", 400),
            }
        )
        return return_data

    def empty_otp_secret():
        return_data.update({"status_code": 404, "otp_secret": ""})
        return return_data

    data = {
        "valid_data": valid_data,
        "invalid_after_expiration_time": invalid_after_expiration_time,
        "invalid_phone_number": invalid_phone_number,
        "empty_phone_number": empty_phone_number,
        "required_phone_number": required_phone_number,
        "incorrect_otp_code": incorrect_otp_code,
        "invalid_otp_code": invalid_otp_code,
        "empty_otp_code": empty_otp_code,
        "required_otp_code": required_otp_code,
        "invalid_otp_secret": invalid_otp_secret,
        "empty_otp_secret": empty_otp_secret,
    }
    return data[request.param]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "verify_otp_data",
    [
        "valid_data",
        "invalid_after_expiration_time",
        "invalid_phone_number",
        "empty_phone_number",
        "required_phone_number",
        "incorrect_otp_code",
        "invalid_otp_code",
        "empty_otp_code",
        "required_otp_code",
        "invalid_otp_secret",
        "empty_otp_secret",
    ],
    indirect=True,
)
def test_verify_otp(verify_otp_data, api_client, mocker):
    client = api_client()
    return_data = verify_otp_data()

    phone_number, status_code = return_data["phone_number"], return_data["status_code"]

    redis_conn = mocker.Mock()
    mocker.patch("user.views.redis_conn", redis_conn)
    mocker.patch("share.utils.redis_conn", redis_conn)

    mocker.patch(
        "user.serializers.check_otp", side_effect=return_data["check_otp_exception"]
    )

    mock_create_tokens = mocker.patch(
        "user.views.UserService.create_tokens",
        return_value={"access": "fake-access-token", "refresh": "fake-refresh-token"},
    )

    resp = client.patch(
        f'/api/users/verify/{return_data["otp_secret"]}/',
        data=return_data["req_json"],
        format="json",
    )

    assert resp.status_code == status_code

    if status_code == 200:
        resp_json = resp.json()
        assert sorted(resp_json.keys()) == sorted(["access", "refresh"])

        user = User.objects.get(phone_number=phone_number)
        mock_create_tokens.assert_called_once_with(user)

        assert user.is_verified
