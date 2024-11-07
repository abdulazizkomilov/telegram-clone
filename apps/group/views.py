from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .permissions import CanUploadMediaPermission
from .models import Group, GroupMessage, GroupPermission
from .serializers import (
    GroupSerializer,
    GroupMessageSerializer,
    GroupMembershipSerializer,
    GroupAddMemberSerializer,
    GroupPermissionSerializer,
)
from share.permissions import IsOwner


class GroupListCreateView(generics.ListCreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        owned_groups = Group.objects.filter(owner=user).order_by()
        member_groups = Group.objects.filter(members=user).order_by()

        return owned_groups.union(member_groups)

    def perform_create(self, serializer):
        GroupPermission.objects.create(group=serializer.save(owner=self.request.user))


class GroupRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    http_method_names = ["get", "delete"]

    def get_queryset(self):
        user = self.request.user
        return Group.objects.filter(owner=user) | Group.objects.filter(members=user)

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("You do not have permission to delete this group.")
        instance.delete()


class GroupMessageCreateView(generics.ListCreateAPIView):
    queryset = GroupMessage.objects.all()
    serializer_class = GroupMessageSerializer
    permission_classes = [permissions.IsAuthenticated, CanUploadMediaPermission]

    def perform_create(self, serializer):
        group_id = self.kwargs.get("pk")
        group = Group.objects.get(pk=group_id)
        serializer.save(sender=self.request.user, group=group)


class JoinLeaveGroupView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "pk"
    http_method_names = ["get", "post", "delete"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return GroupMembershipSerializer

    def post(self, request, *args, **kwargs):
        group = self.get_object()

        if group.is_private:
            return Response(
                {"detail": "This group is private."}, status=status.HTTP_403_FORBIDDEN
            )

        if request.user in group.members.all():
            return Response(
                {"detail": "You are already a member of this group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group.members.add(request.user)
        return Response(
            {"detail": "You have successfully joined the group."},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, *args, **kwargs):
        group = self.get_object()

        if request.user not in group.members.all():
            return Response(
                {"detail": "You are not a member of this group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group.members.remove(request.user)
        return Response(
            {"detail": "You have successfully left the group."},
            status=status.HTTP_200_OK,
        )


class GroupAddMemberView(generics.UpdateAPIView):
    queryset = Group.objects.filter(is_private=True)
    serializer_class = GroupAddMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    http_method_names = ["patch"]

    def get_object(self):
        """Ensure the group ID is valid and the user is the owner."""
        group = super().get_object()
        if not group.is_private:
            raise PermissionDenied("You can only add members to private groups.")
        return group


class GroupPermissionUpdateView(generics.UpdateAPIView):
    queryset = GroupPermission.objects.all()
    serializer_class = GroupPermissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    http_method_names = ["patch"]

    def get_object(self):
        group_id = self.kwargs.get("pk")
        return GroupPermission.objects.get(group_id=group_id)
