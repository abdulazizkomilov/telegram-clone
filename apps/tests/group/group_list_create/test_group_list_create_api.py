import pytest
from unittest.mock import MagicMock
from rest_framework import status
from django.contrib.auth import get_user_model
from group.models import Group, GroupPermission
from share.services import TokenService

User = get_user_model()


@pytest.mark.django_db
def test_list_groups(mocker, api_client, tokens, user_factory, group_factory):
    user = user_factory()

    mock_redis_client = MagicMock()
    mocker.patch.object(TokenService, 'get_redis_client', return_value=mock_redis_client)

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    group = group_factory(owner=user)
    group.members.add(user)
    group.save()

    response = client.get('/api/groups/')

    assert response.status_code == status.HTTP_200_OK

    assert len(response.data['results']) == 1
    assert group.name == response.data['results'][0]['name']
    assert user.first_name == response.data['results'][0]['owner']['first_name']


@pytest.mark.django_db
def test_create_group(mocker, api_client, tokens, user_factory, group_factory):
    user = user_factory()

    mock_redis_client = MagicMock()
    mocker.patch.object(TokenService, 'get_redis_client', return_value=mock_redis_client)

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

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


@pytest.mark.django_db
def test_retrieve_group(mocker, api_client, tokens, user_factory, group_factory):
    owner = user_factory()
    member = user_factory()
    group = group_factory(name='Test Group', owner=owner)
    group.members.add(member)

    mock_redis_client = MagicMock()
    mocker.patch.object(TokenService, 'get_redis_client', return_value=mock_redis_client)

    access, _ = tokens(owner)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.get(f"/api/groups/{group.id}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'Test Group'

    non_owner = user_factory()

    access, _ = tokens(non_owner)
    client = api_client(access)
    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.get(f"/api/groups/{group.id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_group_by_owner(mocker, api_client, tokens, user_factory, group_factory):
    owner = user_factory()
    group = group_factory.create(name='Test Group', owner=owner)

    access, _ = tokens(owner)
    client = api_client(access)

    mock_redis_client = MagicMock()
    mocker.patch.object(TokenService, 'get_redis_client', return_value=mock_redis_client)
    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.delete(f"/api/groups/{group.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Group.objects.filter(id=group.id).exists()


@pytest.mark.django_db
def test_delete_group_by_non_owner(mocker, api_client, tokens, user_factory, group_factory):
    owner = user_factory()
    non_owner = user_factory()
    group = group_factory(name='Test Group', owner=owner)
    group.members.add(non_owner)

    mock_redis_client = MagicMock()
    mocker.patch.object(TokenService, 'get_redis_client', return_value=mock_redis_client)

    access, _ = tokens(non_owner)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.delete(f"/api/groups/{group.id}/")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Group.objects.filter(id=group.id).exists()
