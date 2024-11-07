import factory
import pytest
from rest_framework import status
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from user.models import UserAvatar
from django.utils import timezone
from unittest.mock import MagicMock
from share.services import TokenService
from faker import Faker
from pytest_factoryboy import register

fake = Faker()

AVATAR_UPLOAD_URL = "/api/users/avatars/"


def avatar_detail_url(pk):
    return f"/api/users/avatars/{pk}/"


class AvatarFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "user.UserAvatar"

    id = factory.Faker("uuid4")
    user = factory.SubFactory("tests.factories.user_factory.UserFactory")
    avatar = factory.django.ImageField(color="blue")
    created_at = factory.LazyFunction(lambda: timezone.now())
    updated_at = factory.LazyFunction(lambda: timezone.now())


register(AvatarFactory)


@pytest.fixture
def user_with_avatar(user_factory, avatar_factory):
    """Create a user with an uploaded avatar."""
    user = user_factory.create()
    avatar = avatar_factory.create(user=user)
    return user, avatar


@pytest.fixture
def sample_avatar_file():
    """Generate a valid image file for testing."""
    image = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    return SimpleUploadedFile("avatar.jpg", buffer.read(), content_type="image/jpeg")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "method, url_func, expected_status",
    [
        ("get", lambda avatar: avatar_detail_url(avatar.id), status.HTTP_200_OK),
        (
            "delete",
            lambda avatar: avatar_detail_url(avatar.id),
            status.HTTP_204_NO_CONTENT,
        ),
    ],
)
def test_avatar_operations(
    mocker, tokens, api_client, user_with_avatar, method, url_func, expected_status
):
    """Test retrieving or deleting a user's avatar with valid authentication."""
    user, avatar = user_with_avatar
    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = getattr(client, method)(url_func(avatar))

    assert response.status_code == expected_status
    if method == "delete":
        assert not UserAvatar.objects.filter(id=avatar.id).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "method, expected_status",
    [
        ("get", status.HTTP_401_UNAUTHORIZED),
        ("delete", status.HTTP_401_UNAUTHORIZED),
    ],
)
def test_avatar_unauthenticated(api_client, user_with_avatar, method, expected_status):
    """Test unauthenticated users cannot access or delete avatars."""
    _, avatar = user_with_avatar
    client = api_client()

    response = getattr(client, method)(avatar_detail_url(avatar.id))
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_upload_avatar(mocker, tokens, api_client, user_factory, sample_avatar_file):
    """Test that a user can upload an avatar."""
    user = user_factory.create()

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.post(
        AVATAR_UPLOAD_URL, {"avatar": sample_avatar_file}, format="multipart"
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert "avatar" in data


@pytest.mark.django_db
def test_get_user_avatars(mocker, tokens, api_client, user_with_avatar):
    """Test retrieving a list of user avatars."""
    user, _ = user_with_avatar

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.get(AVATAR_UPLOAD_URL)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
