from rest_framework import permissions


class IsChannelOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only channel owners to perform write operations.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.method in permissions.SAFE_METHODS
