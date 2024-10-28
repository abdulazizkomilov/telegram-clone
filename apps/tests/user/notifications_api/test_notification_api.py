import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from user.models import NotificationPreference

User = get_user_model()


@pytest.mark.django_db
def test_get_notification_preference(api_client, user_factory):
    """Test retrieving notification preferences for the authenticated user."""
    user = user_factory.create()
    client = api_client()
    client.force_authenticate(user=user)

    response = client.get('/api/users/notifications/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "id": response.data["id"],
        "notifications_enabled": False,
        "device_token": None,
    }
    assert NotificationPreference.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_update_notification_preference(api_client, user_factory):
    """Test updating the notification preferences for the authenticated user."""
    user = user_factory.create()
    client = api_client()
    client.force_authenticate(user=user)

    client.get('/api/users/notifications/')

    patch_data = {
        "notifications_enabled": True,
        "device_token": "abc123deviceToken"
    }
    response = client.patch('/api/users/notifications/', patch_data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data["notifications_enabled"] is True
    assert response.data["device_token"] == "abc123deviceToken"

    preference = NotificationPreference.objects.get(user=user)
    assert preference.notifications_enabled is True
    assert preference.device_token == "abc123deviceToken"
