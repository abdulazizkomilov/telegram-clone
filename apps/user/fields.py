import re
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class PhoneNumberField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        self.validate_phone_number(value)
        return value

    def validate_phone_number(self, value):
        pattern = r'^\+998\d{9}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                _("Invalid phone number format. Should start with +998 and have 9 digits after.")
            )


class OtpCodeField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        self.validate_otp_code(value)
        return value

    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(_("Invalid code format. Only str digits are allowed."))
