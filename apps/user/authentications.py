import base64
from typing import Optional
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication, AuthUser, Token
from core.settings import config
from user.models import User
from share.enums import TokenType
from share.services import TokenService


class XApiKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get("X-API-KEY")
        if api_key != config("X_API_KEY"):
            raise AuthenticationFailed(_("Invalid API key"))
        return None, None


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request) -> Optional[tuple[AuthUser, Token]]:
        header = self.get_header(request)
        if header is None:
            return None
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        user, access_token = super().authenticate(request)

        if not self.is_valid_access_token(request.path, user, access_token):
            raise AuthenticationFailed(_("Invalid access token"))

        return user, access_token

    def is_valid_access_token(self, path: str, user: User, access_token: Token) -> bool:
        valid_access_tokens = TokenService.get_valid_tokens(user.id, TokenType.ACCESS)
        if (
            valid_access_tokens
            and str(access_token).encode() not in valid_access_tokens
        ):
            raise AuthenticationFailed(_("Could not validate credentials"))

        return True


class CustomBasicAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Basic "):
            return None
        try:
            header_name, base64_credentials = auth_header.split()
            credentials = base64.b64decode(base64_credentials).decode("utf-8")
            username, password = credentials.split(":", 1)
            user = authenticate(request, username=username, password=password)
            if user is None:
                raise AuthenticationFailed(_("Invalid username or password."))

            return user, None

        except (ValueError, UnicodeDecodeError, AuthenticationFailed):
            return None

    def authenticate_header(self, request):
        return 'Basic realm="API"'
