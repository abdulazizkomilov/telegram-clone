import uuid
import pytest
from faker import Faker
from io import BytesIO
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
from core import settings
from pytest_factoryboy import register

fake = Faker()

if "user" in settings.INSTALLED_APPS:
    from tests.factories.user_factory import UserFactory

    register(UserFactory)

if "chat" in settings.INSTALLED_APPS:
    from tests.factories.chat_factory import ChatFactory

    register(ChatFactory)

if "group" in settings.INSTALLED_APPS:
    from tests.factories.group_factory import GroupFactory

    register(GroupFactory)


@pytest.fixture
def api_client():
    def _api_client(token=None):
        client = APIClient(raise_request_exception=False)
        if token:
            client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        return client

    return _api_client


@pytest.fixture
def generate_test_image():
    """Generate a valid image file for testing."""
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    byte_arr = BytesIO()
    img.save(byte_arr, format="JPEG")
    byte_arr.seek(0)
    return SimpleUploadedFile(
        "test_image.jpg", byte_arr.read(), content_type="image/jpeg"
    )


@pytest.fixture
def generate_test_file():
    """Generate a valid file for testing."""
    return SimpleUploadedFile(
        "test_file.txt", b"file_content", content_type="text/plain"
    )


@pytest.fixture
def tokens():
    def _tokens(user):
        refresh = RefreshToken.for_user(user)
        access = str(getattr(refresh, "access_token"))
        return access, refresh

    return _tokens


@pytest.fixture
def fake_number():
    country_code = "+99890"
    national_number = fake.numerify(text="#######")
    return f"{country_code}{national_number}"


@pytest.fixture
def fake_redis():
    import fakeredis

    return fakeredis.FakeRedis()


@pytest.fixture
def fake_uuid():
    return uuid.uuid4()


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    """Automatically override ENABLE_ES for all tests."""
    monkeypatch.setenv("ENABLE_ES", "False")
