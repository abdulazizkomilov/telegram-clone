from django.http import Http404
from rest_framework import generics, permissions, status, exceptions
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from .models import Channel, ChannelMembership, ChannelMessage, ChannelScheduledMessage
from .serializers import ChannelSerializer, ChannelMembershipSerializer, ChannelMessageSerializer, \
    ChannelMembershipUpdateSerializer, ChannelScheduledMessageSerializer
from .permissions import IsChannelOwnerOrReadOnly
from share.tasks import send_push_notification


class ChannelListCreateView(generics.ListCreateAPIView):
    serializer_class = ChannelSerializer
    queryset = Channel.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Channel.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct().order_by('name')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ChannelRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'delete']

    def get_queryset(self):
        user = self.request.user

        return Channel.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct().order_by('name')

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != self.request.user:
            return Response({"detail": "You are not the owner of this channel."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != self.request.user:
            return Response({"detail": "You are not the owner of this channel."}, status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChannelMembershipListCreateView(generics.ListCreateAPIView):
    serializer_class = ChannelMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post']

    def get_queryset(self):
        channel_id = self.kwargs['pk']
        return ChannelMembership.objects.filter(channel__id=channel_id)

    def perform_create(self, serializer):
        channel = get_object_or_404(Channel, id=self.kwargs['pk'])

        membership = ChannelMembership.objects.filter(
            channel=channel, user=self.request.user
        ).first()

        if channel.channel_type == 'private' and not (
                channel.owner == self.request.user or (membership and membership.role == 'admin')
        ):
            raise exceptions.PermissionDenied(
                "Only the owner or admins can add members to private channels."
            )

        serializer.save(channel=channel)


class ChannelMembershipUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChannelMembershipUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['patch', 'delete']

    def get_queryset(self):
        channel_id = self.kwargs['pk']
        membership_id = self.kwargs['membership_pk']
        queryset = ChannelMembership.objects.filter(channel__id=channel_id, id=membership_id)
        return queryset

    def get_object(self):
        queryset = self.get_queryset()
        if not queryset.exists():
            raise Http404("No ChannelMembership matches the given query.")
        return queryset.first()

    def patch(self, request, *args, **kwargs):
        membership = self.get_object()
        channel = membership.channel

        if channel.owner != request.user and membership.role != 'admin':
            return Response(
                {"detail": "Only the channel owner or admins can update roles."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(membership, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        membership = self.get_object()
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChannelMessageListCreateView(generics.ListCreateAPIView):
    """
    Channel owner can create messages. All members can list messages.
    """
    serializer_class = ChannelMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post']

    def get_queryset(self):
        channel = get_object_or_404(Channel, id=self.kwargs['pk'])
        return channel.messages.all()

    def perform_create(self, serializer):
        channel = get_object_or_404(Channel, id=self.kwargs['pk'])

        if channel.owner != self.request.user:
            raise exceptions.PermissionDenied("Only the owner can create messages.")

        message = serializer.save(user=self.request.user, channel=channel)

        # notification to channel members
        for membership in channel.memberships.all():
            if membership.user != self.request.user:
                send_push_notification.delay(str(membership.user.id), f"New Message in {channel.name}", message.text)


class ChannelMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Channel owners can read, update, and delete messages.
    """
    serializer_class = ChannelMessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsChannelOwnerOrReadOnly]
    http_method_names = ['get', 'patch', 'delete']

    def get_queryset(self):
        channel_id = self.kwargs['pk']
        message_id = self.kwargs['message_id']
        return ChannelMessage.objects.filter(channel__id=channel_id, id=message_id)

    def get_object(self):
        queryset = self.get_queryset()
        if not queryset.exists():
            raise Http404("No ChannelMembership matches the given query.")
        return queryset.first()

    def patch(self, request, *args, **kwargs):
        message = self.get_object()
        if request.user != message.channel.owner:
            return Response({"detail": "You are not the owner of this channel."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(message, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        if request.user != message.channel.owner:
            return Response({"detail": "You are not the owner of this channel."}, status=status.HTTP_403_FORBIDDEN)
        message.delete()
        return super().destroy(request, *args, **kwargs)


class LikeMessageView(generics.GenericAPIView):
    """
    Channel members can like and unlike messages.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, message_id):
        channel = get_object_or_404(Channel, id=pk)
        message = get_object_or_404(ChannelMessage, id=message_id, channel=channel)

        message.likes.add(request.user)
        return Response({"detail": "Message liked."}, status=status.HTTP_200_OK)

    def delete(self, request, pk, message_id):
        channel = get_object_or_404(Channel, id=pk)
        message = get_object_or_404(ChannelMessage, id=message_id, channel=channel)

        message.likes.remove(request.user)
        return Response({"detail": "Like removed."}, status=status.HTTP_200_OK)


class CreateScheduledMessageView(generics.CreateAPIView):
    queryset = ChannelScheduledMessage.objects.all()
    serializer_class = ChannelScheduledMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Ensure the user is the owner of the channel or has the right permissions
        before creating a scheduled message.
        """
        channel_id = self.kwargs['pk']
        try:
            channel = Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            return Response(
                {"detail": "Channel not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if channel.owner != self.request.user:
            return Response(
                {"detail": "You are not authorized to schedule messages for this channel."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save(sender=self.request.user, channel=channel, scheduled_time=now().isoformat())

    def post(self, request, *args, **kwargs):
        """
        Add validation to ensure the scheduled time is not in the past.
        """
        scheduled_time = request.data.get('scheduled_time')
        if scheduled_time and scheduled_time <= now().isoformat():
            return Response(
                {"detail": "Scheduled time must be in the future."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().post(request, *args, **kwargs)
