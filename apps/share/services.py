import datetime
import uuid
from django_redis import get_redis_connection
from redis import Redis

from share.enums import TokenType


class TokenService:
    @classmethod
    def get_redis_client(cls) -> Redis:
        return get_redis_connection("default")

    @classmethod
    def get_valid_tokens(cls, user_id: uuid.UUID, token_type: TokenType) -> set:
        redis_client = cls.get_redis_client()
        token_key = f"user:{user_id}:{token_type}"
        valid_tokens = redis_client.smembers(token_key)
        return valid_tokens

    @classmethod
    def add_token_to_redis(
            cls,
            user_id: uuid.UUID,
            token: str,
            token_type: TokenType,
            expire_time: datetime.timedelta,
    ) -> None:
        redis_client = cls.get_redis_client()

        token_key = f"user:{user_id}:{token_type}"

        # valid_tokens = cls.get_valid_tokens(user_id, token_type)
        # if valid_tokens:
        #     cls.delete_tokens(user_id, token_type)
        redis_client.sadd(token_key, token)
        redis_client.expire(token_key, expire_time)

    @classmethod
    def delete_tokens(cls, user_id: uuid.UUID, token_type: TokenType) -> None:
        redis_client = cls.get_redis_client()
        token_key = f"user:{user_id}:{token_type}"
        valid_tokens = redis_client.smembers(token_key)
        if valid_tokens is not None:
            redis_client.delete(token_key)

