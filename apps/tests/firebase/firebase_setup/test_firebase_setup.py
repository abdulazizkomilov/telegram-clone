import importlib.util
import pytest
import firebase_admin
from core import settings


@pytest.mark.order(1)
def test_firebase_initialization():
    loader = importlib.util.find_spec("firebase_admin")
    assert loader is not None, "firebase_admin is not installed"

    assert firebase_admin._apps is not None, "firebase_admin is not initialized"
    assert settings.firebase_admin is not None
