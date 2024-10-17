from celery import shared_task
from firebase_admin import messaging
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True)
def send_push_notification(self, token, title, body):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )
        response = messaging.send(message)
        logger.info('Successfully sent message: %s', response)
    except Exception as e:
        logger.error('Failed to send push notification: %s', str(e))
