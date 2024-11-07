import pytest
from unittest.mock import patch
from django.utils import timezone
from channel.models import ChannelScheduledMessage, ChannelMessage, Channel
from channel.tasks import send_channel_scheduled_message
from user.models import NotificationPreference


@pytest.mark.django_db
class TestSendChannelScheduledMessageTask:
    @pytest.fixture
    def setup_data(self, user_factory):
        owner = user_factory.create()
        channel = Channel.objects.create(name="Test Channel", owner=owner)

        member_with_notifications = user_factory.create()
        notification_preference = NotificationPreference.objects.create(
            user=member_with_notifications,
            notifications_enabled=True,
            device_token="token1",
        )
        member_with_notifications.notification_preference = notification_preference
        member_with_notifications.save()

        member_without_notifications = user_factory.create()
        channel.memberships.create(user=member_with_notifications)
        channel.memberships.create(user=member_without_notifications)

        # Create a scheduled message
        scheduled_message = ChannelScheduledMessage.objects.create(
            channel=channel,
            sender=owner,
            text="Scheduled message",
            scheduled_time=timezone.now() - timezone.timedelta(minutes=5),
            sent=False,
        )
        return {
            "channel": channel,
            "scheduled_message": scheduled_message,
            "member_with_notifications": member_with_notifications,
            "member_without_notifications": member_without_notifications,
        }

    @patch("channel.tasks.send_push_notification.delay")
    def test_send_scheduled_messages(self, mock_send_push_notification, setup_data):
        send_channel_scheduled_message()

        scheduled_message = ChannelScheduledMessage.objects.get(
            id=setup_data["scheduled_message"].id
        )
        assert scheduled_message.sent is True

        assert ChannelMessage.objects.filter(channel=setup_data["channel"]).count() == 1

        mock_send_push_notification.assert_called_once_with(
            setup_data[
                "member_with_notifications"
            ].notification_preference.device_token,
            f"New Message in {setup_data['channel'].name}",
            setup_data["scheduled_message"].text,
        )
