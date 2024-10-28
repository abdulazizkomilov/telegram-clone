import pytest
from rest_framework import status
from user.models import Contact, User

CONTACT_LIST_CREATE_URL = "/api/users/contacts/"
CONTACT_DELETE_URL = lambda pk: f"/api/users/contacts/{pk}/"
CONTACT_SYNC_URL = "/api/users/contacts/sync/"


@pytest.fixture
def user():
    return User.objects.create(phone_number="+998987654321")


@pytest.fixture
def friend():
    return User.objects.create(phone_number="+998987654322")


@pytest.fixture
def contact(user, friend):
    user = user
    friend = friend
    return Contact.objects.create(user=user, friend=friend, first_name="Friend", last_name="User")


@pytest.mark.django_db
def test_list_contacts(api_client, contact):
    """Test listing contacts for the authenticated user."""

    client = api_client()
    client.force_authenticate(user=contact.user)

    response = client.get(CONTACT_LIST_CREATE_URL)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]["first_name"] == "Friend"
    assert response.data['results'][0]["last_name"] == "User"


@pytest.mark.django_db
def test_create_contact(api_client, tokens, user, friend):
    """Test creating a new contact."""

    client = api_client()
    client.force_authenticate(user=user)

    data = {
        "first_name": "New",
        "last_name": "Friend",
        "phone": friend.phone_number,
    }

    response = client.post(CONTACT_LIST_CREATE_URL, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert Contact.objects.count() == 1
    assert Contact.objects.filter(friend=friend).exists()


@pytest.mark.django_db
def test_delete_contact(api_client, tokens, contact):
    """Test deleting a contact."""
    user = contact.user
    client = api_client()
    client.force_authenticate(user=user)

    response = client.delete(CONTACT_DELETE_URL(contact.id))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Contact.objects.count() == 0


@pytest.mark.django_db
def test_delete_contact_not_owned(api_client, tokens, user_factory, contact):
    """Test that a user cannot delete a contact they don't own."""
    other_user = user_factory.create(username="otheruser", phone_number="+998927654321")

    client = api_client()
    client.force_authenticate(user=other_user)

    response = client.delete(CONTACT_DELETE_URL(contact.id))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_sync_contacts(api_client, tokens, user, friend):
    """Test syncing contacts."""

    client = api_client()
    client.force_authenticate(user=user)

    data = [
        {"phone_number": friend.phone_number, "first_name": friend.first_name, "last_name": friend.last_name},
        {"phone_number": "+998992345672", "first_name": "Not", "last_name": "Found"},
    ]

    response = client.post(CONTACT_SYNC_URL, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data) == 2

    assert response.data[0]["phone_number"] == friend.phone_number
    assert response.data[0]["status"] == "created"

    assert response.data[1]["phone_number"] == "+998992345672"
    assert response.data[1]["status"] == "not found"
