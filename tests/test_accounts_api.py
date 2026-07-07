import pytest


@pytest.mark.django_db
def test_me_anonymous(client):
    response = client.get("/api/accounts/me/")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False, "user": None}


@pytest.mark.django_db
def test_login_then_me_then_logout(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")

    response = client.post(
        "/api/accounts/login/",
        {"username": "alice", "password": "s3cret-pw"},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["user"]["username"] == "alice"

    response = client.get("/api/accounts/me/")
    assert response.json()["authenticated"] is True

    response = client.post("/api/accounts/logout/", content_type="application/json")
    assert response.status_code == 204

    response = client.get("/api/accounts/me/")
    assert response.json()["authenticated"] is False


@pytest.mark.django_db
def test_login_rejects_bad_credentials(client):
    response = client.post(
        "/api/accounts/login/",
        {"username": "nobody", "password": "wrong"},
        content_type="application/json",
    )
    assert response.status_code == 400
