from django.db import models

from user.models import User
from share.enums import ChannelType, ChannelMembershipType
from share.models import BaseModel


class Channel(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    channel_type = models.CharField(max_length=10, choices=ChannelType.choices(), default=ChannelType.PUBLIC)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ChannelMembership(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=ChannelMembershipType.choices(),
                            default=ChannelMembershipType.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'channel']


class ChannelMessage(BaseModel):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    media = models.FileField(upload_to='channel_uploads/', blank=True, null=True)
    file = models.FileField(upload_to='channel_uploads/', blank=True, null=True)
    likes = models.ManyToManyField(User, related_name='channel_liked_messages', blank=True)

    def __str__(self):
        return f"Message from {self.user.username} in {self.channel.name}"


class ChannelScheduledMessage(BaseModel):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    media = models.FileField(upload_to='channel_uploads/', blank=True, null=True)
    file = models.FileField(upload_to='channel_uploads/', blank=True, null=True)
    scheduled_time = models.DateTimeField()
    sent = models.BooleanField(default=False)
