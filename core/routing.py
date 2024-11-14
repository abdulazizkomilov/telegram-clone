from django.urls import path
from chat.consumers import ChatConsumer  # , UserConsumer
from group.consumers import GroupConsumer

websocket_urlpatterns = [
    # path("ws/", UserConsumer.as_asgi()),
    path("ws/chats/<uuid:pk>/", ChatConsumer.as_asgi()),
    path("ws/groups/<uuid:pk>/", GroupConsumer.as_asgi()),
]
