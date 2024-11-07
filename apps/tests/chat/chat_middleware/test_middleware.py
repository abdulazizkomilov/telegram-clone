import pytest
import jwt
from datetime import datetime
from unittest.mock import AsyncMock, patch
from django.contrib.auth.models import AnonymousUser
from user.models import User
from share.middleware import TokenAuthMiddleware


@pytest.mark.django_db
@pytest.mark.asyncio
class TestTokenAuthMiddleware:
    @pytest.fixture
    def valid_token_payload(self):
        return {
            "user_id": 1,
            "exp": datetime.utcnow().timestamp() + 600,
        }

    @pytest.fixture
    def fake_scope(self):
        return {"query_string": b""}

    async def mock_asgi_app(self, scope, receive, send):
        """Mock ASGI app to be used as inner app."""
        return scope

    @pytest.mark.asyncio
    @patch("share.middleware.get_user", AsyncMock(return_value=AnonymousUser()))
    async def test_middleware_no_token(self, fake_scope):
        """Test middleware with no token in the query string."""
        middleware = TokenAuthMiddleware(self.mock_asgi_app)
        await middleware(fake_scope, None, None)

        assert isinstance(
            fake_scope["user"], AnonymousUser
        ), "Expected user to be AnonymousUser."

    @pytest.mark.asyncio
    @patch("share.middleware.jwt.decode")
    @patch("user.models.User.objects.get")
    async def test_valid_token(
        self, mock_get_user, mock_jwt_decode, valid_token_payload, fake_scope
    ):
        """Test middleware with a valid token."""
        mock_jwt_decode.return_value = valid_token_payload
        mock_get_user.return_value = User(
            id="123e4567-e89b-12d3-a456-426655440000", username="+998933333333"
        )

        middleware = TokenAuthMiddleware(self.mock_asgi_app)
        await middleware(fake_scope, None, None)

        assert (
            fake_scope["user"].id == "123e4567-e89b-12d3-a456-426655440000"
        ), "Expected user with ID 1 but got AnonymousUser."

    @pytest.mark.asyncio
    @patch("share.middleware.jwt.decode", side_effect=jwt.ExpiredSignatureError)
    async def test_expired_token(self, mock_jwt_decode, fake_scope):
        """Test middleware with an expired token."""
        middleware = TokenAuthMiddleware(self.mock_asgi_app)
        await middleware(fake_scope, None, None)

        assert isinstance(
            fake_scope["user"], AnonymousUser
        ), "Expected user to be AnonymousUser due to expired token."

    @pytest.mark.asyncio
    @patch("share.middleware.jwt.decode")
    @patch("user.models.User.objects.get", side_effect=User.DoesNotExist)
    async def test_user_not_found(
        self, mock_get_user, mock_jwt_decode, valid_token_payload, fake_scope
    ):
        """Test middleware when the user is not found in the database."""
        mock_jwt_decode.return_value = valid_token_payload

        middleware = TokenAuthMiddleware(self.mock_asgi_app)
        await middleware(fake_scope, None, None)

        assert isinstance(
            fake_scope["user"], AnonymousUser
        ), "Expected user to be AnonymousUser since user doesn't exist."
