import pytest
from django.urls import set_script_prefix


@pytest.fixture(autouse=True)
def _neutralize_ambient_script_name(settings):
    """Make the test suite independent of a developer's ambient
    DJANGO_FORCE_SCRIPT_NAME (set in a local .env for sub-path debugging).

    Django's test ClientHandler never calls set_script_prefix(), so without
    this reverse() inherits whatever django.setup() read from the ambient
    FORCE_SCRIPT_NAME at process start and prefixes every admin/api URL --
    which the SPA catch-all route then swallows, so admin POSTs come back as
    the SPA shell (200) instead of the expected redirect. Tests that need a
    prefix (test_subpath.py, test_spa.py) opt back in explicitly.
    """
    settings.FORCE_SCRIPT_NAME = None
    settings.SCRIPT_NAME = ""
    settings.STATIC_URL = "/static/"
    settings.MEDIA_URL = "/media/"
    settings.SESSION_COOKIE_PATH = "/"
    settings.CSRF_COOKIE_PATH = "/"
    set_script_prefix("/")
