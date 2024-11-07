from rest_framework import permissions
from .models import GroupPermission


class CanUploadMediaPermission(permissions.BasePermission):
    """
    Custom permission to check if the user can upload media files.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        group_id = view.kwargs.get("pk")

        group_permission = GroupPermission.objects.get(group_id=group_id)
        if group_permission and group_permission.can_send_media:
            return True

        return False
