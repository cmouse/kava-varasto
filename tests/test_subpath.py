import pytest
from django.test import override_settings


@pytest.mark.django_db
def test_admin_login_unprefixed_by_default(client):
    response = client.get("/admin/login/")
    assert response.status_code == 200
    assert b'action="/admin/login/"' in response.content
    assert b"/varasto/" not in response.content


@pytest.mark.django_db
@override_settings(FORCE_SCRIPT_NAME="/varasto", STATIC_URL="/varasto/static/")
def test_admin_login_prefixed_under_script_name(client):
    response = client.get("/admin/login/")
    assert response.status_code == 200
    assert b'action="/varasto/admin/login/"' in response.content
    assert b"/varasto/static/" in response.content
