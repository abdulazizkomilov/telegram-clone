import pytest
from django.utils.timezone import now
from user.models import DeviceInfo


@pytest.mark.django_db
def test_track_login_activity_middleware(api_client, user_factory):
    """Test that DeviceInfo is created when a user logs in."""

    user = user_factory.create()

    client = api_client()
    client.force_authenticate(user=user)

    response = client.get('/api/users/profile/',
                          HTTP_X_FORWARDED_FOR='194.23.54.23',
                          HTTP_USER_AGENT='TestDevice')

    assert response.status_code == 200

    device_info = DeviceInfo.objects.filter(user=user, ip_address='194.23.54.23').first()
    assert device_info is not None
    assert device_info.device_name == 'TestDevice'
    assert device_info.last_login.date() == now().date()
    DeviceInfo.objects.all().delete()


@pytest.mark.django_db
def test_device_list_view(api_client, user_factory):
    """Test that the DeviceListView returns the correct devices."""

    user = user_factory.create()
    DeviceInfo.objects.create(user=user, device_name='Device1', ip_address='194.23.54.23')
    DeviceInfo.objects.create(user=user, device_name='Device2', ip_address='192.168.0.1')

    client = api_client()
    client.force_authenticate(user=user)

    response = client.get("/api/users/devices/")

    assert response.status_code == 200

    data = response.data['results']
    assert len(data) == 2
    assert data[0]['device_name'] == 'Device2'
    assert data[1]['device_name'] == 'Device1'
