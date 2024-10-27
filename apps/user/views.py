import hashlib

from django.core.cache import cache
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from django_redis import get_redis_connection
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from share.services import TokenService
from share.enums import TokenType
from core import settings

from .serializers import SignupSerializer, VerifyOTPSerializer, LoginSerializer, UserProfileSerializer, \
    UserAvatarSerializer, DeviceInfoSerializer, ContactSerializer, ContactSyncSerializer, Enable2FASerializer, \
    Verify2FASerializer, NotificationPreferenceSerializer
from .services import UserService
from .models import User, UserAvatar, DeviceInfo, Contact, NotificationPreference
from .permissions import IsVerifiedUser

# from share.throttles import Throttle

redis_conn = get_redis_connection("default")


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

    # throttle_classes = [Throttle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        otp_secret = redis_conn.get(f"{user.phone_number}:otp_secret").decode()

        return Response({
            "phone_number": user.phone_number,
            "otp_secret": otp_secret,
        }, status=status.HTTP_201_CREATED)


class VerifyView(generics.UpdateAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['patch']
    authentication_classes = []

    # throttle_classes = [Throttle]

    def patch(self, request, *args, **kwargs):
        otp_secret = kwargs.get('otp_secret')
        serializer = VerifyOTPSerializer(data=request.data, context={'otp_secret': otp_secret})
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        user = User.objects.get(phone_number=phone_number)
        user.is_verified = True
        user.is_active = True
        user.save()

        if user.is_2fa_enabled:
            cache.set(f'pending_2fa_{user.id}', True, timeout=300)

            return Response({
                "message": "2FA enabled, please verify your password",
                "user_id": user.id
            }, status=status.HTTP_200_OK)

        # redis_conn.delete(f"{phone_number}:otp")
        # redis_conn.delete(f"{phone_number}:otp_secret")
        tokens = UserService.create_tokens(user)
        return Response(tokens, status=status.HTTP_200_OK)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['post']
    authentication_classes = []

    # throttle_classes = [Throttle]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, phone_number=serializer.validated_data['phone_number'], is_active=True,
                                 is_verified=True)
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        otp_secret = redis_conn.get(f"{user.phone_number}:otp_secret").decode()

        return Response({
            "otp_secret": otp_secret,
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsVerifiedUser]
    http_method_names = ['get', 'patch']

    # throttle_classes = [Throttle]

    def get_object(self):
        return self.request.user


class UserAvatarUploadView(generics.ListCreateAPIView):
    serializer_class = UserAvatarSerializer
    permission_classes = [permissions.IsAuthenticated]

    # throttle_classes = [Throttle]

    def get_queryset(self):
        return UserAvatar.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserAvatarRetrieveDestroy(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    # throttle_classes = [Throttle]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserAvatarSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return UserAvatar.objects.none()
        return UserAvatar.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        avatar_id = self.kwargs.get('pk')

        obj = get_object_or_404(UserAvatar, id=avatar_id, user=self.request.user)
        obj.avatar.delete(save=False)
        obj.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    # throttle_classes = [Throttle]

    @extend_schema(responses=None)
    def post(self, request, *args, **kwargs):
        TokenService.add_token_to_redis(
            request.user.id,
            'fake_token',
            TokenType.ACCESS,
            settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME"),
        )
        TokenService.add_token_to_redis(
            request.user.id,
            'fake_token',
            TokenType.REFRESH,
            settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME"),
        )
        return Response({"detail": "Successfully logged out"})


class DeviceListView(generics.ListAPIView):
    serializer_class = DeviceInfoSerializer
    permission_classes = [permissions.IsAuthenticated]

    # throttle_classes = [Throttle]

    def get_queryset(self):
        return DeviceInfo.objects.filter(user=self.request.user)


class ContactListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ContactSerializer

    # throttle_classes = [Throttle]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContactDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Contact.objects.all()

    # throttle_classes = [Throttle]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)


@extend_schema(
    request=ContactSyncSerializer(many=True),
    responses={201: ContactSyncSerializer(many=True)}
)
class ContactSyncView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ContactSyncSerializer
    pagination_class = None

    # throttle_classes = [Throttle]

    def create(self, request, *args, **kwargs) -> Response:
        contacts = request.data
        response_data = []

        for contact_data in contacts:
            phone_number = contact_data.get('phone_number')
            first_name = contact_data.get('first_name', '')
            last_name = contact_data.get('last_name', '')

            friend = User.objects.filter(phone_number=phone_number).first()

            if not friend:
                response_data.append({
                    'phone_number': phone_number,
                    'status': 'not found'
                })
                continue

            existing_contact = Contact.objects.filter(user=request.user, friend=friend).first()

            if existing_contact:
                response_data.append({
                    'phone_number': phone_number,
                    'first_name': existing_contact.first_name,
                    'last_name': existing_contact.last_name,
                    'status': 'already exists'
                })
            else:
                new_contact = Contact.objects.create(
                    user=request.user,
                    friend=friend,
                    first_name=first_name,
                    last_name=last_name
                )
                response_data.append({
                    'phone_number': new_contact.phone_number,
                    'first_name': new_contact.first_name,
                    'last_name': new_contact.last_name,
                    'status': 'created'
                })

        return Response(response_data, status=201)


@extend_schema(
    request=Enable2FASerializer
)
class Enable2FAView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = Enable2FASerializer

    # throttle_classes = [Throttle]

    def post(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        enable_2fa = serializer.validated_data.get('type')

        if enable_2fa:
            otp_secret = serializer.validated_data['otp_secret']
            hashed_secret = hashlib.sha1(otp_secret.encode('utf-8')).hexdigest()
            user.otp_secret = hashed_secret
            user.is_2fa_enabled = True
            user.save()

            return Response({"detail": "2FA enabled."}, status=status.HTTP_200_OK)
        else:
            user.is_2fa_enabled = False
            user.otp_secret = None
            user.save()

            return Response({"detail": "2FA disabled."}, status=status.HTTP_200_OK)


class Verify2FAView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = Verify2FASerializer

    # throttle_classes = [Throttle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = request.data.get('user_id')
        password = request.data.get('password')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)

        hashed_secret = hashlib.sha1(password.encode('utf-8')).hexdigest()
        if hashed_secret != user.otp_secret:
            return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)

        tokens = UserService.create_tokens(user)
        return Response(tokens, status=status.HTTP_200_OK)


class UserStatusView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        user = User.objects.filter(id=user_id).first()
        if user:
            return Response({
                "is_online": user.is_online,
                "last_seen": user.last_seen,
            })
        return Response({"error": "User not found"}, status=404)


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch']

    def get_object(self):
        obj, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
