from django.contrib import admin

from .models import Channel, ChannelMembership, ChannelMessage, ChannelScheduledMessage

admin.site.register(Channel)
admin.site.register(ChannelMembership)
admin.site.register(ChannelMessage)
admin.site.register(ChannelScheduledMessage)
