import pytest
from django.test import override_settings


@pytest.mark.django_db
def test_root_serves_spa_shell(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'<div id="root" data-script-name=""></div>' in response.content
    assert "csrftoken" in response.cookies


@pytest.mark.django_db
def test_client_side_route_serves_spa_shell(client):
    response = client.get("/some/client/route")
    assert response.status_code == 200
    assert b'<div id="root" data-script-name=""></div>' in response.content


@pytest.mark.django_db
@override_settings(FORCE_SCRIPT_NAME="/varasto")
def test_spa_shell_carries_script_name(client):
    response = client.get("/")
    assert b'data-script-name="/varasto"' in response.content


@pytest.mark.django_db
def test_spa_shell_has_no_inline_script(client):
    # The shell's only <script> is the module bundle. An inline block would
    # force a per-mount-point hash into the Content-Security-Policy, so keep
    # script-src 'self' sufficient by keeping the shell free of one.
    response = client.get("/")

    assert b"window.SCRIPT_NAME" not in response.content
    assert response.content.count(b"<script") == response.content.count(b"<script type=\"module\" src=")
