from celery import shared_task
from .models import ScheduledMessage, Message
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger

from .serializers import MessageSerializer

logger = get_task_logger(__name__)


@shared_task
def send_scheduled_message():
    logger.info("Running scheduled message task.")
    try:
        now = timezone.now()
        scheduled_messages = ScheduledMessage.objects.filter(scheduled_time__lte=now, sent=False)

        if not scheduled_messages.exists():
            logger.info("No scheduled messages to send.")
            return

        logger.info(f"Found {scheduled_messages.count()} scheduled messages to send.")

        for scheduled_message in scheduled_messages:
            message = Message.objects.create(
                chat=scheduled_message.chat,
                sender=scheduled_message.sender,
                text=scheduled_message.text,
                sent_at=timezone.now()
            )

            scheduled_message.sent = True
            scheduled_message.save()

            logger.info(f"Message sent: {message.text}")

            serializer = MessageSerializer(message)

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat__{scheduled_message.chat.id}',
                {
                    'type': 'chat_message',
                    'text': serializer.data
                }
            )
            logger.info(f"Message sent: {message.text}")
    except Exception as e:
        logger.error(f"Error in send_scheduled_message task: {str(e)}")
