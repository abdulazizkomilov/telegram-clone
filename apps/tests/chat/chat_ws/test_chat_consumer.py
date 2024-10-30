# import pytest
# from channels.testing import WebsocketCommunicator
# from core.asgi import application
# from user.models import User
# from chat.models import Chat, Message
# from channels.db import database_sync_to_async
# import asyncio
#
#
# @database_sync_to_async
# def create_user(phone_number):
#     return User.objects.create(phone_number=phone_number, is_verified=True, is_active=True)
#
#
# @database_sync_to_async
# def create_chat(owner, user):
#     return Chat.objects.create(owner=owner, user=user)
#
#
# @database_sync_to_async
# def count_messages_in_chat(chat):
#     return Message.objects.filter(chat=chat).count()
#
#
# @pytest.mark.django_db
# @pytest.mark.asyncio
# async def test_chat_consumer(tokens):
#     user1 = await create_user("+998987654321")
#     user2 = await create_user("+998987654322")
#     chat = await create_chat(user1, user2)
#
#     access, _ = tokens(user1)
#     communicator = WebsocketCommunicator(application, f"/ws/chat/{chat.id}/?token={access}")
#     connected, _ = await communicator.connect()
#     assert connected
#
#     message_data = {
#         "text": "test message for get status"
#     }
#
#     await communicator.send_json_to({
#         "action": "create_message",
#         "request_id": "11",
#         "data": message_data,
#         "pk": str(chat.id)
#     })
#
#     await asyncio.sleep(0.2)
#
#     message_count = await count_messages_in_chat(chat)
#     assert message_count == 1, f"Expected 1 message but got {message_count}"
#
#     await communicator.send_json_to({
#         "action": "get_messages",
#         "request_id": "12",
#         "pk": str(chat.id)
#     })
#
#     response = await communicator.receive_json_from()
#
#     assert response['action'] == 'get_messages'
#     await communicator.disconnect()
