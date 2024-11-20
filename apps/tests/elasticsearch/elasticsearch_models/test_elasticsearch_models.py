import pytest
from django.conf import settings
from apps.share.documents import UserIndex, GroupIndex, ChannelIndex
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_user_index_registered():
    """Test if UserIndex is correctly registered with Elasticsearch."""
    if settings.ENABLE_ES:
        assert UserIndex._index._name == "users"
        assert "phone_number" in UserIndex._doc_type.mapping
        assert "first_name" in UserIndex._doc_type.mapping
        assert "last_name" in UserIndex._doc_type.mapping
    else:
        assert not hasattr(UserIndex, "_index")


@pytest.mark.django_db
def test_group_index_registered():
    """Test if GroupIndex is correctly registered with Elasticsearch."""
    if settings.ENABLE_ES:
        assert GroupIndex._index._name == "groups"
        assert "name" in GroupIndex._doc_type.mapping
    else:
        assert not hasattr(GroupIndex, "_index")


@pytest.mark.django_db
def test_channel_index_registered():
    """Test if ChannelIndex is correctly registered with Elasticsearch."""
    if settings.ENABLE_ES:
        assert ChannelIndex._index._name == "channels"
        assert "name" in ChannelIndex._doc_type.mapping
        assert "description" in ChannelIndex._doc_type.mapping
    else:
        assert not hasattr(ChannelIndex, "_index")
