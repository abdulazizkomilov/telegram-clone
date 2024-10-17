from django.db import models
from django.utils import timezone

from share.models import BaseModel
from user.models import User


class Chat(BaseModel):
    owner = models.ForeignKey(User, related_name='owner', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='user', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('owner', 'user')

    def __str__(self):
        return f"Chat {self.id}"


class ChatParticipant(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_participants')
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='participants')
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'chat']

    def __str__(self):
        return f"{self.user} in {self.chat}"


class Message(BaseModel):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="chat_images/", blank=True, null=True)
    file = models.FileField(upload_to="chat_files/", blank=True, null=True)
    sent_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    liked_by = models.ManyToManyField(User, related_name='liked_messages', blank=True)

    def __str__(self):
        return f"Message {self.id} in {self.chat} by {self.sender}"


class ScheduledMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    scheduled_time = models.DateTimeField()
    sent = models.BooleanField(default=False)
