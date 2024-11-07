from django.db import models
from share.models import BaseModel
from django.utils import timezone
from user.models import User


class Group(BaseModel):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User, related_name="owned_groups", on_delete=models.CASCADE
    )
    members = models.ManyToManyField(User, related_name="group_members", blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class GroupParticipant(BaseModel):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user} in {self.group}"


class GroupMessage(BaseModel):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="group_messages"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="group_images/", blank=True, null=True)
    file = models.FileField(upload_to="group_files/", blank=True, null=True)
    sent_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    liked_by = models.ManyToManyField(
        User, related_name="group_liked_messages", blank=True
    )

    def __str__(self):
        return f"Message {self.id} in {self.group.name} by {self.sender}"


class GroupScheduledMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    scheduled_time = models.DateTimeField()
    sent = models.BooleanField(default=False)


class GroupPermission(BaseModel):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="permissions"
    )
    can_send_messages = models.BooleanField(default=True)
    can_send_media = models.BooleanField(default=False)
