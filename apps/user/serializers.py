from rest_framework import serializers
from .models import User, UserAvatar, DeviceInfo, Contact, NotificationPreference
from share.utils import generate_otp, check_otp
from share.tasks import send_sms_task, send_email_task
from user.fields import PhoneNumberField, OtpCodeField


class SignupSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField()

    class Meta:
        model = User
        fields = ["phone_number"]

    def validate(self, attrs):
        if not attrs.get("phone_number"):
            raise Exception(400, "Phone number required!")
        return attrs

    def create(self, validated_data):
        phone_number = validated_data.get("phone_number")

        user, created = User.objects.get_or_create(phone_number=phone_number)

        if user.is_verified:
            raise serializers.ValidationError(
                {"phone_number": "User with this phone number already exists."}
            )

        otp_code, otp_secret = generate_otp(phone_number, expire_in=2 * 60)
        send_email_task.delay(otp_code)
        send_sms_task.delay(phone_number, otp_code)
        print("otp_code", otp_code)
        return user


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()
    otp_code = OtpCodeField()

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        otp_code = attrs.get("otp_code")
        otp_secret = self.context.get("otp_secret")

        check_otp(phone_number, otp_code, otp_secret)

        return attrs


class LoginSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        otp_code, otp_secret = generate_otp(phone_number, expire_in=5 * 60)
        send_email_task.delay(otp_code)
        send_sms_task.delay(phone_number, otp_code)
        print("otp_code", otp_code)

        return attrs


class UserSerializer(serializers.ModelSerializer):
    id = serializers.CharField()

    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "user_name",
            "bio",
            "birth_date",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id", "user", "phone_number"]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "user_name",
            "bio",
            "birth_date",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id", "user", "phone_number"]

    def validate(self, attrs):
        """Check if the user_name is unique only when provided."""
        user_name = attrs.get("user_name")

        # Skip validation if user_name is not being updated
        if user_name is not None:
            if not user_name.strip():
                raise serializers.ValidationError(
                    {"user_name": "User name cannot be empty."}
                )

            # Ensure the username is unique, excluding the current user
            if (
                User.objects.filter(user_name=user_name)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"user_name": "User with this user name already exists."}
                )

        return attrs


class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAvatar
        fields = ["id", "avatar"]
        read_only_fields = ["id"]


class DeviceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceInfo
        fields = ["device_name", "ip_address", "last_login"]


class ContactSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)

    class Meta:
        model = Contact
        fields = ["id", "username", "first_name", "last_name", "phone_number", "phone"]
        read_only_fields = ["id", "username", "phone_number"]

    def validate_phone(self, value):
        try:
            phone = User.objects.get(phone_number=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                f"User with phone number '{value}' does not exist."
            )
        return phone

    def create(self, validated_data):
        friend_phone_number = validated_data.pop("phone")

        try:
            friend = User.objects.get(phone_number=friend_phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "phone": [
                        f"User with phone number '{friend_phone_number}' does not exist."
                    ]
                }
            )

        if Contact.objects.filter(
            user=self.context["request"].user, friend=friend
        ).exists():
            raise serializers.ValidationError(
                {"friend": [f"You already have {friend.phone_number} as a contact."]}
            )

        contact = Contact.objects.create(friend=friend, **validated_data)
        return contact


class ContactSyncSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)


class Enable2FASerializer(serializers.Serializer):
    type = serializers.BooleanField()
    otp_secret = serializers.CharField(allow_blank=True)


class Verify2FASerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    password = serializers.CharField()


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ["id", "notifications_enabled", "device_token"]
