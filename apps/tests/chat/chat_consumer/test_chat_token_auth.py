# import pytest
# import jwt
# from datetime import datetime, timedelta
# from unittest.mock import patch, AsyncMock
# from channels.db import database_sync_to_async
# from channels.testing import WebsocketCommunicator
# from django.contrib.auth import get_user_model
# from chat.consumers import ChatConsumer
# from channels.layers import get_channel_layer
# from chat.models import Chat
# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.conf import settings
# from django.urls import path
# from chat.middleware import JwtAuthMiddlewareStack
#
# User = get_user_model()
#
# # Application setup with the middleware for testing
# application = ProtocolTypeRouter({
#     "websocket": JwtAuthMiddlewareStack(
#         URLRouter([
#             path("ws/chat/<str:pk>/", ChatConsumer.as_asgi()),
#         ])
#     ),
# })
#
#
# @pytest.mark.django_db(transaction=True)
# @pytest.mark.asyncio
# class TestChatConsumer:
#
#     @database_sync_to_async
#     def create_user(self, phone_number):
#         return User.objects.create(phone_number=phone_number, is_verified=True, is_active=True)
#
#     @database_sync_to_async
#     def create_chat(self, owner, user):
#         return Chat.objects.create(owner=owner, user=user)
#
#     @pytest.fixture
#     async def chat(self):
#         owner = await self.create_user("+998987654321")
#         participant = await self.create_user("+998987654322")
#         chat_instance = await self.create_chat(owner, participant)
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
#     @pytest.mark.asyncio
#     @patch('redis.asyncio.client.Redis')
#     @patch("chat.middleware.jwt.decode")
#     async def test_valid_token_and_chat_connection(self, mock_jwt_decode, mock_redis, chat):
#         """Test successful connection with a valid token and chat ID."""
#         mock_connection = AsyncMock()
#         mock_redis.return_value = mock_connection
#
#         chat_instance, owner, _ = await chat
#
#         token_payload = await self.generate_token_payload(owner.id)
#         mock_jwt_decode.return_value = token_payload
#
#         token = self.generate_jwt_token(token_payload)
#         communicator = WebsocketCommunicator(application, f"/ws/chat/{chat_instance.pk}/?token={token}")
#
#         # Attempt the connection
#         connected, _ = await communicator.connect()
#         assert connected, "WebSocket connection failed with a valid token."
#         print("75 Connected: ", connected)
#
#         # Capture any initial message sent by the connection
#         initial_response = await communicator.receive_json_from()
#         print("Initial response:", initial_response)
#
#         # Send a message to the group
#         channel_layer = get_channel_layer()
#         await channel_layer.group_send(
#             f"chat__{chat_instance.pk}",
#             {
#                 "type": "chat_message",
#                 "text": "Test message"
#             }
#         )
#
#         # Verify the 'new_message' action from the message event
#         response = await communicator.receive_json_from()
#         print("85 Response:", response)
#         assert response["action"] == "get_messages", "The action should be 'get_messages'."
#         assert response["data"] == "Test message", "Incorrect message received by WebSocket client."
#
#         # Disconnect and clean up
#         await communicator.disconnect()
#
#     @pytest.mark.asyncio
#     async def test_invalid_token(self, chat):
#         invalid_token = "invalid.token.value"
#         chat_instance, _, _ = await chat
#
#         communicator = WebsocketCommunicator(
#             application,
#             f"/ws/chat/{chat_instance.pk}/?token={invalid_token}",
#         )
#
#         connected, _ = await communicator.connect()
#         assert not connected, "Connection should not succeed with an invalid token."
#
#         # Disconnect and clean up
#         await communicator.disconnect()
