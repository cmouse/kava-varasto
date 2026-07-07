import pytest
from django.test import override_settings


@pytest.mark.django_db
def test_root_serves_spa_shell(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'<div id="root"></div>' in response.content
    assert "csrftoken" in response.cookies


@pytest.mark.django_db
def test_client_side_route_serves_spa_shell(client):
    response = client.get("/some/client/route")
    assert response.status_code == 200
    assert b'<div id="root"></div>' in response.content


@pytest.mark.django_db
@override_settings(FORCE_SCRIPT_NAME="/varasto")
def test_spa_shell_carries_script_name(client):
    response = client.get("/")
    assert b'window.SCRIPT_NAME = "/varasto"' in response.content
