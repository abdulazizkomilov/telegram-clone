from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from drf_spectacular.extensions import OpenApiAuthenticationExtension

from .authentications import CustomBasicAuthentication, CustomJWTAuthentication


class CustomJWTAuthenticationScheme(SimpleJWTScheme):
    name = "CustomJWTAuth"
    target_class = CustomJWTAuthentication


class CustomBasicAuthenticationScheme(OpenApiAuthenticationExtension):
    name = "CustomBasicAuth"
    target_class = CustomBasicAuthentication

    def map(self, auto_schema, direction):
        if direction == "output":
            return {
                "type": "http",
                "scheme": "basic",
                "description": "Custom Basic Authentication",
            }
        return super().map(auto_schema, direction)

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "basic",
            "description": "Custom Basic Authentication",
        }
