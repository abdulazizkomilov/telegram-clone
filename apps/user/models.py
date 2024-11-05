from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone

from share.models import BaseModel
from .managers import UserManager


class User(AbstractBaseUser, BaseModel, PermissionsMixin):
    phone_number = models.CharField(max_length=15, unique=True)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    user_name = models.CharField(max_length=50, null=True, blank=True)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    is_2fa_enabled = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=32, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "user"
        verbose_name = "User"
        ordering = ['-created_at']

    def __str__(self):
        return self.first_name or self.username or self.phone_number

    def update_last_seen(self):
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class UserAvatar(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="avatar")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    class Meta:
        db_table = "user_avatar"
        verbose_name = "User Avatar"
        ordering = ['-created_at']


class DeviceInfo(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_name = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    last_login = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.device_name} - {self.ip_address}"

    class Meta:
        db_table = "device_info"
        verbose_name = "Device Info"
        ordering = ['-created_at']


class Contact(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_by')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.friend.username} -> {self.friend.username}"

    @property
    def phone_number(self):
        return self.friend.phone_number

    @property
    def username(self):
        return self.friend.user_name

    class Meta:
        db_table = "contact"
        verbose_name = "Contact"
        ordering = ['-added_at']


class NotificationPreference(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    notifications_enabled = models.BooleanField(default=False)
    device_token = models.CharField(max_length=555, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Notifications: {'Enabled' if self.notifications_enabled else 'Disabled'}, Token: {self.device_token or 'None'}"
