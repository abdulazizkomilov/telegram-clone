from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "is_active",
        "is_verified",
        "username",
        "first_name",
        "last_name",
    )
    list_display_links = ("phone_number",)
    ordering = ("-created_at",)
