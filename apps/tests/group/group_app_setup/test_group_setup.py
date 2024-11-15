import pytest
from django.conf import settings
from django.utils import timezone
from group.models import (
    Group,
    GroupParticipant,
    GroupMessage,
    GroupScheduledMessage,
    GroupPermission,
)

MODEL_NAME = "Group"
APP_NAME = "group"


@pytest.mark.django_db
def test_group_app_exists():
    try:
        import group  # noqa
    except ImportError:
        assert False, f"{APP_NAME} app folder missing"

    assert APP_NAME in settings.INSTALLED_APPS, f"{APP_NAME} model not installed"


@pytest.mark.django_db
def test_group_model_exists():
    """Test that the group model exists and is installed."""
    try:
        from group.models import Group  # noqa
    except ImportError:
        assert False, f"{MODEL_NAME} model not found"


@pytest.mark.django_db
def test_create_group(user_factory):
    user = user_factory.create()
    group = Group.objects.create(name="Test Group", owner=user, is_private=False)
    group.members.add(user)
    group.save()

    assert group is not None, f"{MODEL_NAME} model not found"
    assert group.members.count() == 1
    assert group.owner == user
    assert group.name == "Test Group"
    assert group.is_private is False


@pytest.mark.django_db
def test_group_participant_creation(user_factory):
    user = user_factory.create()
    group = Group.objects.create(name="Test Group", owner=user, is_private=False)
    participant = GroupParticipant.objects.create(group=group, user=user)

    assert participant is not None
    assert participant.group == group
    assert participant.user == user
    assert isinstance(participant.joined_at, timezone.datetime)


@pytest.mark.django_db
def test_group_message_creation(user_factory):
    user = user_factory.create()
    group = Group.objects.create(name="Test Group", owner=user, is_private=False)
    group.members.add(user)

    message = GroupMessage.objects.create(
        group=group, sender=user, text="Test Message", is_read=False
    )

    assert message is not None
    assert message.group == group
    assert message.sender == user
    assert message.text == "Test Message"
    assert message.is_read is False
    assert isinstance(message.sent_at, timezone.datetime)


@pytest.mark.django_db
def test_group_scheduled_message_creation(user_factory):
    user = user_factory.create()
    group = Group.objects.create(name="Test Group", owner=user, is_private=False)

    scheduled_message = GroupScheduledMessage.objects.create(
        group=group,
        sender=user,
        text="Scheduled Test Message",
        scheduled_time=timezone.now(),
        sent=False,
    )

    assert scheduled_message is not None
    assert scheduled_message.group == group
    assert scheduled_message.sender == user
    assert scheduled_message.text == "Scheduled Test Message"
    assert not scheduled_message.sent
    assert isinstance(scheduled_message.scheduled_time, timezone.datetime)


@pytest.mark.django_db
def test_group_permission_creation(user_factory):
    user = user_factory.create()
    group = Group.objects.create(name="Test Group", owner=user, is_private=False)

    permission = GroupPermission.objects.create(
        group=group, can_send_messages=True, can_send_media=False
    )

    assert permission is not None
    assert permission.group == group
    assert permission.can_send_messages is True
    assert permission.can_send_media is False
