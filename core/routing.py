from django.urls import path
from chat.consumers import UserConsumer, ChatConsumer
from group.consumers import GroupConsumer

websocket_urlpatterns = [
    path("ws/", UserConsumer.as_asgi()),
    path('ws/chat/<uuid:pk>/', ChatConsumer.as_asgi()),
    path('ws/group/<uuid:pk>/', GroupConsumer.as_asgi()),
]
