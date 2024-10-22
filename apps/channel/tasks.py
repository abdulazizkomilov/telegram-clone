from celery import shared_task
from .models import ChannelScheduledMessage, ChannelMessage
from django.utils import timezone
from celery.utils.log import get_task_logger

from .serializers import ChannelMessageSerializer

logger = get_task_logger(__name__)


@shared_task
def send_channel_scheduled_message():
    logger.info("Running scheduled message task.")
    try:
        now = timezone.now()
        scheduled_messages = ChannelScheduledMessage.objects.filter(scheduled_time__lte=now, sent=False)

        if not scheduled_messages.exists():
            logger.info("No scheduled messages to send.")
            return

        logger.info(f"Found {scheduled_messages.count()} scheduled messages to send.")

        for scheduled_message in scheduled_messages:
            message = ChannelMessage.objects.create(
                channel=scheduled_message.channel,
                user=scheduled_message.sender,
                text=scheduled_message.text,
                media=scheduled_message.media,
                file=scheduled_message.file
            )

            scheduled_message.sent = True
            scheduled_message.save()

            logger.info(f"Message sent: {message.text}")

            serializer = ChannelMessageSerializer(message)

            # notification to channel members

            logger.info(f"Message sent: {message.text}")
    except Exception as e:
        logger.error(f"Error in send_scheduled_message task: {str(e)}")
