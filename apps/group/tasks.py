from celery import shared_task
from .models import GroupScheduledMessage, GroupMessage
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger

from .serializers import GroupMessageSerializer

logger = get_task_logger(__name__)


@shared_task
def send_group_scheduled_message():
    logger.info("Running scheduled message task.")
    try:
        now = timezone.now()
        scheduled_messages = GroupScheduledMessage.objects.filter(
            scheduled_time__lte=now, sent=False
        )

        if not scheduled_messages.exists():
            logger.info("No scheduled messages to send.")
            return

        logger.info(f"Found {scheduled_messages.count()} scheduled messages to send.")

        for scheduled_message in scheduled_messages:
            message = GroupMessage.objects.create(
                group=scheduled_message.group,
                sender=scheduled_message.sender,
                text=scheduled_message.text,
                sent_at=timezone.now(),
            )

            scheduled_message.sent = True
            scheduled_message.save()

            logger.info(f"Message sent: {message.text}")

            serializer = GroupMessageSerializer(message)

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"group__{scheduled_message.group.id}",
                {"type": "group_message", "text": serializer.data},
            )
            logger.info(f"Message sent: {message.text}")
    except Exception as e:
        logger.error(f"Error in send_scheduled_message task: {str(e)}")
