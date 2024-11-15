from rest_framework.permissions import BasePermission


class GroupOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == "GET":
            return obj.owner == request.user or request.user in obj.members.all()

        if request.method == "DELETE":
            return obj.owner == request.user

        return False


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner
