import pytest
from rest_framework import status
from unittest.mock import MagicMock
from share.services import TokenService
from user.models import Contact, User

CONTACT_LIST_CREATE_URL = "/api/users/contacts/"
CONTACT_SYNC_URL = "/api/users/contacts/sync/"


def contact_delete_url(pk):
    return f"/api/users/contacts/{pk}/"


@pytest.fixture
def user():
    return User.objects.create(phone_number="+998987654001")


@pytest.fixture
def friend():
    return User.objects.create(phone_number="+998987654999")


@pytest.fixture
def contact(user, friend):
    user = user
    friend = friend
    return Contact.objects.create(
        user=user, friend=friend, first_name="Friend", last_name="User"
    )


@pytest.mark.django_db
def test_list_contacts(mocker, tokens, api_client, contact):
    """Test listing contacts for the authenticated user."""

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(contact.user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.get(CONTACT_LIST_CREATE_URL)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["first_name"] == "Friend"
    assert response.data["results"][0]["last_name"] == "User"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "phone, expected_status, should_create_contact",
    [
        ("friend.phone_number", status.HTTP_201_CREATED, True),
        ("user.phone_number", status.HTTP_400_BAD_REQUEST, False),
    ],
)
def test_create_contact(
    mocker,
    api_client,
    tokens,
    user,
    friend,
    phone,
    expected_status,
    should_create_contact,
):
    """Test creating a new contact with different scenarios."""

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)
    mock_redis_client.smembers.return_value = {access.encode()}

    data = {"first_name": "New", "last_name": "Friend", "phone": eval(phone)}

    response = client.post(CONTACT_LIST_CREATE_URL, data, format="json")

    assert response.status_code == expected_status
    assert Contact.objects.count() == (1 if should_create_contact else 0)
    assert Contact.objects.filter(friend=friend).exists() == should_create_contact


@pytest.mark.django_db
def test_delete_contact(mocker, api_client, tokens, contact):
    """Test deleting a contact."""
    user = contact.user

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.delete(contact_delete_url(contact.id))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Contact.objects.count() == 0


@pytest.mark.django_db
def test_delete_contact_not_owned(mocker, api_client, tokens, user_factory, contact):
    """Test that a user cannot delete a contact they don't own."""
    other_user = user_factory.create(username="otheruser", phone_number="+998927654121")

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(other_user)
    client = api_client(access)

    mock_redis_client.smembers.return_value = {access.encode()}

    response = client.delete(contact_delete_url(contact.id))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_sync_contacts(mocker, api_client, tokens, user, friend, user_factory):
    """Test syncing contacts."""

    friend_2 = user_factory.create()
    Contact.objects.create(user=user, friend=friend_2)

    mock_redis_client = MagicMock()
    mocker.patch.object(
        TokenService, "get_redis_client", return_value=mock_redis_client
    )

    access, _ = tokens(user)
    client = api_client(access)

    data = {
        "first_name": "New",
        "last_name": "Friend",
        "phone": friend_2.phone_number,
    }
    client.post(CONTACT_LIST_CREATE_URL, data, format="json")

    mock_redis_client.smembers.return_value = {access.encode()}

    data = [
        {
            "phone_number": friend.phone_number,
            "first_name": friend.first_name,
            "last_name": friend.last_name,
        },
        {"phone_number": "+99899234444", "first_name": "Not", "last_name": "Found"},
        {"phone_number": user.phone_number, "first_name": "Me", "last_name": "Me"},
        {
            "phone_number": friend_2.phone_number,
            "first_name": "Friend",
            "last_name": "2",
        },
    ]

    response = client.post(CONTACT_SYNC_URL, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data) == 4

    assert response.data[0]["phone_number"] == friend.phone_number
    assert response.data[0]["status"] == "created"

    assert response.data[1]["phone_number"] == "+99899234444"
    assert response.data[1]["status"] == "not found"

    assert response.data[2]["phone_number"] == user.phone_number
    assert response.data[2]["status"] == "self"

    assert response.data[3]["phone_number"] == friend_2.phone_number
    assert response.data[3]["status"] == "already exists"
