from django.urls import path
from . import views

urlpatterns = [
    path("", views.GroupListCreateView.as_view(), name="group-list"),
    path("<uuid:pk>/", views.GroupRetrieveDestroyView.as_view(), name="group-detail"),
    path(
        "<uuid:pk>/messages/",
        views.GroupMessageCreateView.as_view(),
        name="group-message-create",
    ),
    path(
        "<uuid:pk>/memberships/",
        views.JoinLeaveGroupView.as_view(),
        name="join-leave-group",
    ),
    path("<uuid:pk>/members/", views.GroupAddMemberView.as_view(), name="add-members"),
    path(
        "<uuid:pk>/permissions/",
        views.GroupPermissionUpdateView.as_view(),
        name="update-group-permission",
    ),
]
