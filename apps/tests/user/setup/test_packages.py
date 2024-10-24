import importlib.util
import pytest
from core import settings


@pytest.mark.order(1)
def test_via_importlib():
    loader = importlib.util.find_spec('decouple')
    assert loader is not None, "decouple is not installed"


@pytest.mark.order(2)
def test_via_importlib():
    loader = importlib.util.find_spec('rest_framework')
    assert loader is not None, "djangorestframework is not installed"


@pytest.mark.order(3)
def test_via_importlib():
    loader = importlib.util.find_spec('rest_framework_simplejwt')
    assert loader is not None, "rest_framework_simplejwt is not installed"


@pytest.mark.order(4)
@pytest.mark.django_db
def test_rest_framework():
    assert 'rest_framework' in settings.INSTALLED_APPS, "rest_framework package is not added to INSTALLED_APPS"
    assert 'DEFAULT_PERMISSION_CLASSES' in settings.REST_FRAMEWORK.keys(), "DEFAULT_PERMISSION_CLASSES not in REST_FRAMEWORK"


@pytest.mark.order(5)
@pytest.mark.django_db
def test_rest_framework():
    assert 'rest_framework_simplejwt' in settings.INSTALLED_APPS, "rest_framework_simplejwt package is not added to INSTALLED_APPS"
