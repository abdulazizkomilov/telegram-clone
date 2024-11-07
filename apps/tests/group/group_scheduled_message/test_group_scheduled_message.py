import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from group.models import GroupScheduledMessage, GroupMessage
from group.tasks import send_group_scheduled_message
from group.serializers import GroupMessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestSendGroupScheduledMessageTask:
    @pytest.fixture
    def group(self, group_factory):
        return group_factory.create()

    @pytest.fixture
    def user(self, user_factory):
        return user_factory.create()

    @pytest.fixture
    def scheduled_message(self, group, user):
        return GroupScheduledMessage.objects.create(
            group=group,
            sender=user,
            text="Scheduled group message text",
            scheduled_time=timezone.now() - timezone.timedelta(minutes=1),
            sent=False,
        )

    @patch("group.tasks.GroupMessage.objects.create")
    @patch("group.tasks.get_channel_layer")
    def test_send_group_scheduled_message(
        self, mock_get_channel_layer, mock_message_create, scheduled_message
    ):
        mock_message = MagicMock(spec=GroupMessage)
        mock_message_create.return_value = mock_message
        mock_message.text = scheduled_message.text
        mock_message.sent_at = timezone.now()

        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        send_group_scheduled_message()

        mock_message_create.assert_called_once()
        created_message = mock_message_create.return_value
        assert created_message.text == scheduled_message.text

        scheduled_message.refresh_from_db()
        assert scheduled_message.sent is True

        serializer = GroupMessageSerializer(mock_message)
        mock_channel_layer.group_send.assert_called_once_with(
            f"group__{scheduled_message.group.id}",
            {"type": "group_message", "text": serializer.data},
        )

    @patch("group.tasks.get_task_logger")
    def test_send_group_scheduled_message_no_messages(self, mock_get_task_logger):
        GroupScheduledMessage.objects.all().delete()
        mock_logger = mock_get_task_logger.return_value

        send_group_scheduled_message()

        mock_logger.info.assert_not_called()
