import pytest
from django.conf import settings

MODEL_NAME = "Group"
APP_NAME = "group"


@pytest.mark.order(1)
@pytest.mark.django_db
def test_group_app_exists():
    try:
        import group  # noqa
    except ImportError:
        assert False, f"{APP_NAME} app folder missing"

    assert APP_NAME in settings.INSTALLED_APPS, f"{APP_NAME} model not installed"


@pytest.mark.order(2)
@pytest.mark.django_db
def test_group_model_exists():
    """Test that the group model exists and is installed."""
    try:
        from group.models import Group  # noqa
    except ImportError:
        assert False, f"{MODEL_NAME} model not found"


@pytest.mark.order(3)
@pytest.mark.django_db
def test_create_group(user_factory):
    user = user_factory.create()
    from group.models import Group

    group = Group.objects.create(name="Test Group", owner=user, is_private=False)
    group.members.add(user)
    group.save()
    assert group is not None, f"{MODEL_NAME} model not found"
    assert group.members.count() == 1
