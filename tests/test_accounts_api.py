import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_me_anonymous(client):
    response = client.get("/api/accounts/me/")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False, "user": None}


@pytest.mark.django_db
def test_me_sets_csrf_cookie(client):
    # The frontend's first call on every page load is GET /me/ (see
    # useCurrentUser()), so this is what primes the csrftoken cookie the
    # login form and language switcher need -- regardless of whether the
    # shell HTML came from Django's spa view or the Vite dev server.
    response = client.get("/api/accounts/me/")
    assert "csrftoken" in response.cookies


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


@pytest.mark.django_db
def test_me_reports_must_change_password_flag(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw", must_change_password=True)
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    response = client.get("/api/accounts/me/")

    assert response.json()["user"]["must_change_password"] is True


@pytest.mark.django_db
def test_change_password_requires_current_password(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    response = client.post(
        "/api/accounts/change-password/",
        {"current_password": "wrong-pw", "new_password": "Str0ngP@ssw0rd!"},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "current_password" in response.json()


@pytest.mark.django_db
def test_change_password_success_clears_flag_and_keeps_session(client, django_user_model):
    user = django_user_model.objects.create_user(username="alice", password="s3cret-pw", must_change_password=True)
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    response = client.post(
        "/api/accounts/change-password/",
        {"current_password": "s3cret-pw", "new_password": "Str0ngP@ssw0rd!"},
        content_type="application/json",
    )
    assert response.status_code == 200, response.json()
    assert response.json()["user"]["must_change_password"] is False

    response = client.get("/api/accounts/me/")
    assert response.json()["authenticated"] is True

    user.refresh_from_db()
    assert user.must_change_password is False
    assert user.check_password("Str0ngP@ssw0rd!")


@pytest.mark.django_db
def test_change_password_rejects_weak_new_password(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    response = client.post(
        "/api/accounts/change-password/",
        {"current_password": "s3cret-pw", "new_password": "12345678"},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "new_password" in response.json()


@pytest.mark.django_db
def test_admin_add_user_sets_must_change_password(admin_client, django_user_model):
    response = admin_client.post(
        reverse("admin:accounts_user_add"),
        {
            "username": "newstaff",
            "password1": "Str0ngP@ssw0rd!",
            "password2": "Str0ngP@ssw0rd!",
            "usable_password": "true",
        },
    )
    assert response.status_code == 302, response.content

    user = django_user_model.objects.get(username="newstaff")
    assert user.must_change_password is True


@pytest.mark.django_db
def test_admin_reset_password_sets_must_change_password(admin_client, django_user_model):
    user = django_user_model.objects.create_user(username="bob", password="OldPass123!")
    assert user.must_change_password is False

    response = admin_client.post(
        reverse("admin:auth_user_password_change", args=[user.pk]),
        {"password1": "NewStr0ngP@ss!", "password2": "NewStr0ngP@ss!"},
    )
    assert response.status_code == 302, response.content

    user.refresh_from_db()
    assert user.must_change_password is True
