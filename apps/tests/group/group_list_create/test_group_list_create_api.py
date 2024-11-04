import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from group.models import Group, GroupPermission

User = get_user_model()


@pytest.mark.django_db
def test_list_groups(api_client, user_factory, group_factory):
    user = user_factory()

    client = api_client()
    client.force_authenticate(user=user)

    group = group_factory(owner=user)
    group.members.add(user)
    group.save()

    response = client.get('/api/groups/')

    assert response.status_code == status.HTTP_200_OK

    assert len(response.data['results']) == 1
    assert group.name == response.data['results'][0]['name']
    assert user.first_name == response.data['results'][0]['owner']['first_name']


@pytest.mark.django_db
def test_create_group(api_client, user_factory):
    user = user_factory()

    client = api_client()
    client.force_authenticate(user=user)

    group_data = {
        'name': 'New Group',
        'is_private': True
    }

    response = client.post('/api/groups/', group_data, format='json')

    assert response.status_code == status.HTTP_201_CREATED

    new_group = Group.objects.get(name='New Group')
    assert new_group.owner.first_name == user.first_name
    assert new_group.is_private is True

    group_permission = GroupPermission.objects.filter(group=new_group).exists()
    assert group_permission
