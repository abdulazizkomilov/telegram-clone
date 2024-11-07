from django.contrib import admin
from .models import (
    Group,
    GroupMessage,
    GroupParticipant,
    GroupScheduledMessage,
    GroupPermission,
)

admin.site.register(Group)
admin.site.register(GroupMessage)
admin.site.register(GroupParticipant)
admin.site.register(GroupScheduledMessage)
admin.site.register(GroupPermission)
