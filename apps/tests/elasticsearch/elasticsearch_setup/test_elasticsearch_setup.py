import importlib.util
import pytest
from core import settings


@pytest.mark.order(1)
def test_via_importlib():
    loader = importlib.util.find_spec("django_elasticsearch_dsl")
    assert loader is not None, "elasticsearch_dsl is not installed"


@pytest.mark.order(2)
@pytest.mark.django_db
def test_elasticsearch_setup_exists():
    assert (
        "django_elasticsearch_dsl" in settings.INSTALLED_APPS
    ), "django_elasticsearch_dsl package is not added to INSTALLED_APPS"
    assert settings.ELASTICSEARCH_DSL is not None
    assert settings.ELASTICSEARCH_DSL["default"] is not None
    assert settings.ENABLE_ES is not None
