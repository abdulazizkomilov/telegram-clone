import uuid
import pytest
from faker import Faker
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from core import settings
from pytest_factoryboy import register

fake = Faker()

if "user" in settings.INSTALLED_APPS:
    from tests.factories.user_factory import UserFactory

    register(UserFactory)

if "chat" in settings.INSTALLED_APPS:
    from tests.factories.chat_factory import ChatFactory

    register(ChatFactory)


@pytest.fixture
def api_client():
    def _api_client(token=None):
        client = APIClient(raise_request_exception=False)
        if token:
            client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return client

    return _api_client


@pytest.fixture
def tokens():
    def _tokens(user):
        refresh = RefreshToken.for_user(user)
        access = str(getattr(refresh, 'access_token'))
        return access, refresh

    return _tokens


@pytest.fixture
def fake_number():
    country_code = '+99890'
    national_number = fake.numerify(text="#######")
    return f"{country_code}{national_number}"


@pytest.fixture
def fake_redis():
    import fakeredis
    return fakeredis.FakeRedis()


@pytest.fixture
def fake_uuid():
    return uuid.uuid4()
