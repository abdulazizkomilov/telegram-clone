from django.http import Http404
from rest_framework import generics, permissions, status, exceptions
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Channel, ChannelMembership, ChannelMessage
from .serializers import ChannelSerializer, ChannelMembershipSerializer, ChannelMessageSerializer, \
    ChannelMembershipUpdateSerializer


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
