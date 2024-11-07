from django.urls import path
from . import views

urlpatterns = [
    path("", views.ChannelListCreateView.as_view(), name="channel-list"),
    path(
        "<uuid:pk>/",
        views.ChannelRetrieveUpdateDestroyView.as_view(),
        name="channel-detail",
    ),
    path(
        "<uuid:pk>/memberships/",
        views.ChannelMembershipListCreateView.as_view(),
        name="membership-list-create",
    ),
    path(
        "<uuid:pk>/memberships/<uuid:membership_pk>/",
        views.ChannelMembershipUpdateDestroyView.as_view(),
        name="membership-detail",
    ),
    path(
        "<uuid:pk>/messages/",
        views.ChannelMessageListCreateView.as_view(),
        name="channel-message-list-create",
    ),
    path(
        "<uuid:pk>/messages/schedule/",
        views.CreateScheduledMessageView.as_view(),
        name="channel-message-create-schedule",
    ),
    path(
        "<uuid:pk>/messages/<uuid:message_id>/",
        views.ChannelMessageDetailView.as_view(),
        name="channel-message-detail",
    ),
    path(
        "<uuid:pk>/messages/<uuid:message_id>/like/",
        views.LikeMessageView.as_view(),
        name="like-message",
    ),
]
