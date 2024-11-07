import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def signup_data(request, user_factory, mocker):
    user = user_factory.create(is_verified=False)
    req_json = {"phone_number": user.phone_number}

    def valid_data():
        redis_conn = mocker.Mock()
        redis_conn.exists.return_value = False
        redis_conn.get.return_value = b"123111"
        return 201, redis_conn, req_json

    def phone_number_exists():
        user.is_verified = True
        user.save()
        req_json.update({"phone_number": user.phone_number})
        return 400, None, req_json

    def invalid_phone_number():
        req_json.update({"phone_number": "invalid"})
        return 400, None, req_json

    def empty_phone_number():
        req_json.update({"phone_number": ""})
        return 400, None, req_json

    def required_phone_number():
        req_json.pop("phone_number")
        return 400, None, req_json

    data = {
        "valid_data": valid_data,
        "phone_number_exists": phone_number_exists,
        "invalid_phone_number": invalid_phone_number,
        "empty_phone_number": empty_phone_number,
        "required_phone_number": required_phone_number,
    }
    return data[request.param]()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "signup_data",
    [
        "valid_data",
        "phone_number_exists",
        "invalid_phone_number",
        "empty_phone_number",
        "required_phone_number",
    ],
    indirect=True,
)
def test_signup(signup_data, api_client, mocker):
    client = api_client()
    status_code, redis_conn, req_json = signup_data

    mocker.patch("user.views.redis_conn", redis_conn)
    mocker.patch("share.utils.redis_conn", redis_conn)

    mocker.patch("user.serializers.send_sms_task", return_value=None)
    mocker.patch("user.serializers.send_email_task", return_value=None)

    resp = client.post("/api/users/register/", data=req_json, format="json")

    assert resp.status_code == status_code

    if status_code == 201:
        resp_json = resp.json()
        assert sorted(resp_json.keys()) == sorted(["phone_number", "otp_secret"])

        user = User.objects.get(phone_number=req_json["phone_number"])
        assert user.is_verified is False

        redis_conn.get.assert_called_once_with(f"{req_json['phone_number']}:otp_secret")
