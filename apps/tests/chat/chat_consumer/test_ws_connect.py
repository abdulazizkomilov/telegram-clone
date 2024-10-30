import pytest
from channels.testing import WebsocketCommunicator
from core.asgi import application
from user.models import User
from chat.models import Chat
from channels.db import database_sync_to_async


@database_sync_to_async
def create_user(phone_number):
    return User.objects.create(phone_number=phone_number, is_verified=True, is_active=True)


@database_sync_to_async
def create_chat(owner, user):
    return Chat.objects.create(owner=owner, user=user)


# @pytest.mark.django_db
# @pytest.mark.asyncio
# async def test_chat_consumer(tokens):
#     user1 = await create_user("+998987654321")
#     user2 = await create_user("+998987654322")
#     chat = await create_chat(user1, user2)
#
#     access, _ = tokens(user1)
#     communicator = WebsocketCommunicator(application, f"/ws/chat/{chat.id}/")
#     connected, _ = await communicator.connect()
#     assert connected
#
#     await communicator.disconnect()


"""
from channels.generic.websocket import WebsocketConsumer

from .models import Chat
from .serializers import ChatSerializer

class ChatConsumer(WebsocketConsumer):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    lookup_field = "pk"

    async def connect(self):
        await self.accept()

    async def disconnect(self, code):
        await super().disconnect(code)


Post:
https://medium.com/@adabur/introduction-to-django-channels-and-websockets-cb38cd015e29

https://medium.com/django-unleashed/websockets-based-apis-with-django-real-time-communication-made-easy-2122b49720bf

import json
from channels.generic.websocket import WebsocketConsumer
class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
    def disconnect(self, close_code):
        pass
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        self.send(text_data=json.dumps({
            'message': message
        }))
"""
