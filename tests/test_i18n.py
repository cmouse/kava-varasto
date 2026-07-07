import pytest


@pytest.mark.django_db
def test_admin_login_defaults_to_finnish(client):
    response = client.get("/admin/login/")
    assert response.status_code == 200
    assert "Kirjaudu sisään".encode() in response.content


@pytest.mark.django_db
def test_admin_login_switches_to_english_via_accept_language(client):
    response = client.get("/admin/login/", HTTP_ACCEPT_LANGUAGE="en")
    assert response.status_code == 200
    assert b"Log in" in response.content
    assert "Kirjaudu sisään".encode() not in response.content
