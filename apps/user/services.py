from typing import Union
from rest_framework.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from share.enums import TokenType
from share.services import TokenService
from user.models import User


class UserService:
    @classmethod
    def authenticate(cls, phone_number: str) -> Union[ValidationError, User, None]:
        user = authenticate(username=phone_number, password=None)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return user

    @classmethod
    def create_tokens(
        cls, user: User, access: str = None, refresh: str = None
    ) -> dict[str, str]:
        if not access or not refresh:
            refresh = RefreshToken.for_user(user)
            access = str(getattr(refresh, "access_token"))
            refresh = str(refresh)
        valid_access_tokens = TokenService.get_valid_tokens(
            user_id=user.id, token_type=TokenType.ACCESS
        )
        if valid_access_tokens:
            TokenService.add_token_to_redis(
                user.id,
                access,
                TokenType.ACCESS,
                settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME"),
            )

        valid_refresh_tokens = TokenService.get_valid_tokens(
            user_id=user.id, token_type=TokenType.REFRESH
        )
        if valid_refresh_tokens:
            TokenService.add_token_to_redis(
                user.id,
                refresh,
                TokenType.REFRESH,
                settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME"),
            )
        return {"access": access, "refresh": refresh}
