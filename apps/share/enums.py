from enum import Enum


class BaseEnum(Enum):
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]

    @classmethod
    def values(cls):
        return [choice.value for choice in cls]


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class ChannelType(BaseEnum):
    PUBLIC = "public"
    PRIVATE = "private"


class ChannelMembershipType(BaseEnum):
    ADMIN = "admin"
    MEMBER = "member"
