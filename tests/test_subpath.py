from contextlib import contextmanager

import pytest
from django.test import override_settings
from django.urls import get_script_prefix, set_script_prefix


@contextmanager
def script_name(prefix, **settings_overrides):
    """override_settings(FORCE_SCRIPT_NAME=...) alone isn't enough here:
    the script prefix used to render URLs is normally set per-request by
    the real WSGI/ASGI handler, but Django's test Client goes through
    ClientHandler, which never calls set_script_prefix(). It's instead
    whatever django.setup() set once at process start from the ambient
    FORCE_SCRIPT_NAME, so tests must set/restore it explicitly to be
    independent of that ambient value.
    """
    previous = get_script_prefix()
    set_script_prefix(prefix)
    try:
        with override_settings(**settings_overrides):
            yield
    finally:
        set_script_prefix(previous)


@pytest.mark.django_db
def test_admin_login_unprefixed_by_default(client):
    with script_name("/", FORCE_SCRIPT_NAME=None, STATIC_URL="/static/"):
        response = client.get("/admin/login/")
    assert response.status_code == 200
    assert b'action="/admin/login/"' in response.content
    assert b"/varasto/" not in response.content


@pytest.mark.django_db
def test_admin_login_prefixed_under_script_name(client):
    with script_name("/varasto/", FORCE_SCRIPT_NAME="/varasto", STATIC_URL="/varasto/static/"):
        response = client.get("/admin/login/")
    assert response.status_code == 200
    assert b'action="/varasto/admin/login/"' in response.content
    assert b"/varasto/static/" in response.content


@pytest.mark.django_db
def test_forced_password_change_redirect_is_prefixed(client, django_user_model):
    # ForcePasswordChangeMiddleware builds its target from reverse("spa"),
    # so the redirect has to land inside the mount point -- a bare
    # /account/password would leave the app entirely under a sub-path.
    django_user_model.objects.create_superuser(
        username="root", password="s3cret-pw", must_change_password=True
    )
    client.login(username="root", password="s3cret-pw")

    with script_name("/varasto/", FORCE_SCRIPT_NAME="/varasto", STATIC_URL="/varasto/static/"):
        response = client.get("/admin/")

    assert response.status_code == 302
    assert response.headers["Location"] == "/varasto/account/password"
