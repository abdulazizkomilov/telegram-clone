import pytest
import uuid
from unittest.mock import patch, MagicMock
from django.utils import timezone
from chat.models import ScheduledMessage, Message
from chat.tasks import send_scheduled_message
from chat.serializers import MessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestSendScheduledMessageTask:
    @pytest.fixture
    def owner(self, user_factory):
        return user_factory.create()

    @pytest.fixture
    def user(self, user_factory):
        return user_factory.create()

    @pytest.fixture
    def chat(self, chat_factory, owner, user):
        return chat_factory.create(owner=owner, user=user)

    @pytest.fixture
    def scheduled_message(self, chat, owner):
        return ScheduledMessage.objects.create(
            chat=chat,
            sender=owner,
            text="Scheduled message text",
            scheduled_time=timezone.now() - timezone.timedelta(minutes=1),
            sent=False,
        )

    @patch("chat.tasks.Message.objects.create")
    @patch("chat.tasks.get_channel_layer")
    def test_send_scheduled_message(
        self, mock_get_channel_layer, mock_message_create, scheduled_message
    ):
        mock_message = MagicMock(spec=Message)
        mock_message_create.return_value = mock_message
        uuid_num = uuid.uuid4()
        mock_message.id = uuid_num
        mock_message.text = scheduled_message.text
        mock_message.sent_at = timezone.now()

        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        send_scheduled_message()

        mock_message_create.assert_called_once()
        created_message_id = mock_message_create.return_value.id
        assert created_message_id == uuid_num

        scheduled_message.refresh_from_db()
        assert scheduled_message.sent is True

        serializer = MessageSerializer(mock_message)

        mock_channel_layer.group_send.assert_called_once_with(
            f"chat__{scheduled_message.chat.id}",
            {"type": "chat_message", "text": serializer.data},
        )

    @patch("chat.tasks.get_task_logger")
    def test_send_scheduled_message_no_messages(self, mock_get_task_logger):
        ScheduledMessage.objects.all().delete()
        mock_logger = mock_get_task_logger.return_value

        send_scheduled_message()
        assert mock_logger.info.call_count == 0
