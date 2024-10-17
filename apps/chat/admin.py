from django.contrib import admin
from .models import Chat, Message, ChatParticipant, ScheduledMessage

admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(ChatParticipant)
admin.site.register(ScheduledMessage)
