# import pytest
# import jwt
# import asyncio
# from datetime import datetime, timedelta
# from unittest.mock import patch, AsyncMock
# from channels.db import database_sync_to_async
# from channels.testing import WebsocketCommunicator
# from django.contrib.auth import get_user_model
# from chat.consumers import ChatConsumer
# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.conf import settings
# from django.urls import path
# from share.middleware import JwtAuthMiddlewareStack
# from channels.layers import get_channel_layer
#
# User = get_user_model()
#
# # Define the application routing
# application = ProtocolTypeRouter({
#     "websocket": JwtAuthMiddlewareStack(
#         URLRouter([
#             path("ws/chat/<str:pk>/", ChatConsumer.as_asgi()),
#         ])
#     ),
# })
#
#
# @pytest.fixture
# def channel_layer(settings):
#     """Override the channel layer to use an in-memory channel layer for testing."""
#     settings.CHANNEL_LAYERS = {
#         "default": {
#             "BACKEND": "channels.layers.InMemoryChannelLayer",
#         },
#     }
#     return get_channel_layer()
#
#
# @pytest.mark.django_db(transaction=True)
# @pytest.mark.asyncio
# class TestChatConsumer:
#
#     @database_sync_to_async
#     def create_user(self, user_factory):
#         return user_factory.create()
#
#     @database_sync_to_async
#     def create_chat(self, chat_factory, owner, user):
#         return chat_factory.create(owner=owner, user=user)
#
#     @pytest.fixture
#     async def chat(self, user_factory, chat_factory):
#         owner = await self.create_user(user_factory)
#         participant = await self.create_user(user_factory)
#         chat_instance = await self.create_chat(chat_factory, owner, participant)
#         return chat_instance, owner, participant
#
#     async def generate_token_payload(self, owner_id):
#         return {
#             "user_id": str(owner_id),
#             "exp": datetime.utcnow() + timedelta(minutes=10),
#         }
#
#     def generate_jwt_token(self, payload):
#         return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
#
#     @patch("share.middleware.jwt.decode")
#     @pytest.mark.asyncio
#     async def test_send_message_to_group(self, mock_jwt_decode, chat, channel_layer):
#         # Mock JWT payload and group send method
#         mock_jwt_decode.return_value = await self.generate_token_payload(chat[1].id)  # Mocked token payload
#         chat_instance, owner, _ = await chat
#
#         token = self.generate_jwt_token(mock_jwt_decode.return_value)
#         communicator = WebsocketCommunicator(application, f"/ws/chat/{chat_instance.pk}/?token={token}")
#
#         connected, _ = await communicator.connect()
#         assert connected, "WebSocket connection failed with a valid token."
#
#         message_data = {
#             "action": "create_message",
#             "request_id": "1",
#             "pk": str(chat_instance.pk),
#             "data": {"text": "Hello, group!"}
#         }
#         await communicator.send_json_to(message_data)
#
#         # Allow time for the group send to happen
#         await asyncio.sleep(0.2)
#
#         group_name = f'chat__{chat_instance.pk}'
#         expected_message = {
#             'type': 'chat_message',
#             'text': message_data["data"]["text"]
#         }
#
#         # Verify that the group_send was called correctly
#         assert channel_layer.groups[group_name].send.call_count == 1  # Check if group_send was called once
#         assert channel_layer.groups[group_name].send.call_args[0][0] == expected_message  # Check the message sent
#
#         await communicator.disconnect()
#
#     @patch("share.middleware.jwt.decode")
#     @patch("channels.layers.get_channel_layer")
#     @pytest.mark.asyncio
#     async def test_send_message_to_group(self, mock_get_channel_layer, mock_jwt_decode, chat):
#         mock_jwt_decode.return_value = await self.generate_token_payload(chat[1].id)  # Mocked token payload
#         chat_instance, owner, _ = await chat
#
#         # Mock the channel layer's group_send method
#         mock_channel_layer = AsyncMock()
#         mock_get_channel_layer.return_value = mock_channel_layer
#
#         token = self.generate_jwt_token(mock_jwt_decode.return_value)
#         communicator = WebsocketCommunicator(application, f"/ws/chat/{chat_instance.pk}/?token={token}")
#
#         connected, _ = await communicator.connect()
#         assert connected, "WebSocket connection failed with a valid token."
#
#         message_data = {
#             "action": "create_message",
#             "request_id": "1",
#             "pk": str(chat_instance.pk),
#             "data": {"text": "Hello, group!"}
#         }
#         await communicator.send_json_to(message_data)
#
#         # Allow time for the group send to happen
#         await asyncio.sleep(0.2)
#
#         group_name = f'chat__{chat_instance.pk}'
#         expected_message = {
#             'type': 'chat_message',
#             'text': message_data["data"]["text"]
#         }
#
#         # Verify that the group_send was called correctly
#         mock_channel_layer.group_send.assert_called_once_with(group_name,
#                                                               expected_message)  # Check if group_send was called once with the expected message
#
#         await communicator.disconnect()
