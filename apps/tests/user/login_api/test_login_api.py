import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def login_data(request, user_factory, fake_number):
    phone_number = fake_number
    user = user_factory.create(
        phone_number=phone_number, is_active=True, is_verified=True
    )

    def valid_phone_number():
        return (
            200,
            {"phone_number": user.phone_number},
        )

    def required_phone_number():
        return (400, {})

    def empty_phone_number():
        return (
            400,
            {"phone_number": ""},
        )

    def invalid_phone_number():
        return (
            400,
            {"phone_number": "invalid"},
        )

    def not_found_phone_number():
        return (
            404,
            {"phone_number": "+998911234567"},
        )

    data = {
        "valid_phone_number": valid_phone_number,
        "required_phone_number": required_phone_number,
        "empty_phone_number": empty_phone_number,
        "invalid_phone_number": invalid_phone_number,
        "not_found_phone_number": not_found_phone_number,
    }
    return data[request.param]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_data",
    [
        "valid_phone_number",
        "required_phone_number",
        "empty_phone_number",
        "invalid_phone_number",
        "not_found_phone_number",
    ],
    indirect=True,
)
def test_login(login_data, api_client, mocker):
    status_code, req_json = login_data()

    redis_conn = mocker.Mock()
    redis_conn.get.return_value = b"d3kj8kJks9j38h93nus32asb3fc-2c963f67m3i3"
    mocker.patch("user.views.redis_conn", redis_conn)

    mocker.patch("user.serializers.send_sms_task", return_value=None)
    mocker.patch("user.serializers.send_email_task", return_value=None)
    mocker.patch(
        "user.serializers.generate_otp", return_value=("otp_code", "otp_secret")
    )

    resp = api_client().post("/api/users/login/", data=req_json)

    assert resp.status_code == status_code
    if status_code == 200:
        resp_json = resp.json()
        assert "otp_secret" in resp_json
