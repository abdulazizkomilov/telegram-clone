import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

MODEL_NAME = "User"
APP_NAME = "user"
EXPECTED_DB_TABLE = "user"
EXPECTED_VERBOSE_NAME = "User"
EXPECTED_VERBOSE_NAME_PLURAL = "Users"
EXPECTED_ORDERING = ["-created_at"]


@pytest.mark.order(1)
@pytest.mark.django_db
def test_users_app_exists():
    """Test that the user app exists and is installed."""
    try:
        import user  # noqa
    except ImportError:
        assert False, f"{APP_NAME} app folder missing"

    assert APP_NAME in settings.INSTALLED_APPS, f"{APP_NAME} app not installed"


@pytest.mark.order(2)
@pytest.mark.django_db
def test_custom_user_model():
    """Test the custom user model and its fields."""

    assert (
        settings.AUTH_USER_MODEL == f"{APP_NAME}.{MODEL_NAME}"
    ), f"{MODEL_NAME} model not set"

    User = get_user_model()
    assert User is not None, f"{MODEL_NAME} model not found"

    # Check model metadata
    assert (
        User._meta.db_table == EXPECTED_DB_TABLE
    ), f"{MODEL_NAME} model db_table not set"
    assert (
        User._meta.verbose_name == EXPECTED_VERBOSE_NAME
    ), f"{MODEL_NAME} model verbose_name not set"
    assert (
        User._meta.verbose_name_plural == EXPECTED_VERBOSE_NAME_PLURAL
    ), f"{MODEL_NAME} model verbose_name_plural not set"
    assert (
        User._meta.ordering == EXPECTED_ORDERING
    ), f"{MODEL_NAME} model ordering not set"

    # Create a user instance
    user = User.objects.create(
        phone_number="+998930000000",
        first_name="Abdulaziz",
        last_name="Komilov",
        user_name="abdulaziz",
        bio="bio",
        birth_date="2000-01-01",
        is_verified=True,
        is_active=True,
        is_online=True,
    )

    # Assertions to validate user creation
    assert user is not None, f"{MODEL_NAME} model not created"
    assert user.first_name == "Abdulaziz", f"{MODEL_NAME} model first_name not set"
    assert user.last_name == "Komilov", f"{MODEL_NAME} model last_name not set"
    assert (
        user.phone_number == "+998930000000"
    ), f"{MODEL_NAME} model phone_number not set"
    assert user.is_active is True, f"{MODEL_NAME} model is_active not set"
    assert user.is_online is True, f"{MODEL_NAME} model is_online not set"
    assert user.is_verified is True, f"{MODEL_NAME} model is_verified not set"
    assert user.user_name == "abdulaziz", f"{MODEL_NAME} model user_name not set"
    assert user.bio == "bio", f"{MODEL_NAME} model bio not set"
    assert user.birth_date == "2000-01-01", f"{MODEL_NAME} model birth_date not set"
    assert user.created_at is not None, f"{MODEL_NAME} model created_at not set"
