from django.urls import path
from .views import ChatListCreateView, ChatView, MessageListCreateView

urlpatterns = [
    path("", ChatListCreateView.as_view(), name="chat-list"),
    path("<uuid:pk>/", ChatView.as_view(), name="chat-detail"),
    path("<uuid:pk>/messages/", MessageListCreateView.as_view(), name="chat-messages"),
]
