from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry
from django.contrib.auth import get_user_model
from group.models import Group
from channel.models import Channel
from core import settings

User = get_user_model()

if settings.ENABLE_ES:
    @registry.register_document
    class UserIndex(Document):
        class Index:
            name = 'users'

        class Django:
            model = User
            fields = [
                'phone_number',
                'first_name',
                'last_name',
            ]


    @registry.register_document
    class GroupIndex(Document):
        class Index:
            name = 'groups'

        class Django:
            model = Group
            fields = ['name']


    @registry.register_document
    class ChannelIndex(Document):
        class Index:
            name = 'channels'

        class Django:
            model = Channel
            fields = ['name', 'description']
else:
    class UserIndex:
        pass


    class GroupIndex:
        pass


    class ChannelIndex:
        pass
