import pytest
from django.test import Client
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
def test_login_rejects_request_without_csrf_token(django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")
    csrf_client = Client(enforce_csrf_checks=True)

    response = csrf_client.post(
        "/api/accounts/login/",
        {"username": "alice", "password": "s3cret-pw"},
        content_type="application/json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_login_succeeds_with_csrf_token(django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")
    csrf_client = Client(enforce_csrf_checks=True)
    # GET /me/ primes the csrftoken cookie the SPA sends back as X-CSRFToken.
    csrf_client.get("/api/accounts/me/")
    token = csrf_client.cookies["csrftoken"].value

    response = csrf_client.post(
        "/api/accounts/login/",
        {"username": "alice", "password": "s3cret-pw"},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 200, response.json()
    assert response.json()["authenticated"] is True


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


@pytest.mark.django_db
def test_flagged_user_cannot_use_the_api_until_password_is_changed(client, django_user_model):
    # The SPA gate (Layout.jsx) is a rendering decision; the session itself
    # must be refused by the server until the issued password is rotated.
    django_user_model.objects.create_user(username="alice", password="s3cret-pw", must_change_password=True)
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    assert client.get("/api/inventory/equipment/").status_code == 403
    assert client.get("/api/loans/").status_code == 403

    response = client.post(
        "/api/accounts/change-password/",
        {"current_password": "s3cret-pw", "new_password": "Str0ngP@ssw0rd!"},
        content_type="application/json",
    )
    assert response.status_code == 200, response.json()

    assert client.get("/api/inventory/equipment/").status_code == 200


@pytest.mark.django_db
def test_flagged_user_can_still_log_out(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw", must_change_password=True)
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    assert client.post("/api/accounts/logout/", content_type="application/json").status_code == 204


@pytest.mark.django_db
def test_flagged_staff_user_is_redirected_out_of_the_admin(client, django_user_model):
    # The admin is a second way into the same data and has no notion of the
    # flag, so the middleware has to send these sessions to the SPA form.
    django_user_model.objects.create_superuser(
        username="root", password="s3cret-pw", must_change_password=True
    )
    client.login(username="root", password="s3cret-pw")

    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert response.headers["Location"] == "/account/password"


@pytest.mark.django_db
def test_flagged_staff_user_can_still_reach_admin_logout(client, django_user_model):
    django_user_model.objects.create_superuser(
        username="root", password="s3cret-pw", must_change_password=True
    )
    client.login(username="root", password="s3cret-pw")

    # Django's admin logout is POST-only.
    response = client.post(reverse("admin:logout"))

    assert response.status_code == 200
    assert client.get("/api/accounts/me/").json()["authenticated"] is False


@pytest.mark.django_db
def test_api_login_is_rate_limited(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")

    for _ in range(10):
        response = client.post(
            "/api/accounts/login/",
            {"username": "alice", "password": "wrong"},
            content_type="application/json",
        )
        assert response.status_code == 400

    response = client.post(
        "/api/accounts/login/",
        {"username": "alice", "password": "s3cret-pw"},
        content_type="application/json",
    )
    assert response.status_code == 429


@pytest.mark.django_db
def test_admin_login_is_rate_limited(client, django_user_model):
    django_user_model.objects.create_superuser(username="root", password="s3cret-pw")
    url = reverse("admin:login")

    for _ in range(10):
        assert client.post(url, {"username": "root", "password": "wrong"}).status_code == 200

    response = client.post(url, {"username": "root", "password": "s3cret-pw"})
    assert response.status_code == 429
    assert "Retry-After" in response.headers


@pytest.mark.django_db
def test_both_login_forms_share_one_throttle_budget(client, django_user_model):
    # Same passwords, same accounts -- guessing at one form must spend the
    # other's budget too, or the limit is trivially doubled.
    django_user_model.objects.create_superuser(username="root", password="s3cret-pw")

    for _ in range(10):
        client.post(
            "/api/accounts/login/",
            {"username": "root", "password": "wrong"},
            content_type="application/json",
        )

    assert client.post(reverse("admin:login"), {"username": "root", "password": "wrong"}).status_code == 429


@pytest.mark.django_db
def test_csrf_rejected_admin_posts_do_not_spend_the_login_budget(django_user_model):
    # Counted in the request phase, ten junk POSTs from a passer-by would lock
    # out every real user behind the same address without ever guessing a
    # password. CsrfViewMiddleware has to reject them first.
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")
    csrf_client = Client(enforce_csrf_checks=True)

    for _ in range(10):
        response = csrf_client.post(reverse("admin:login"), {"username": "zz", "password": "zz"})
        assert response.status_code == 403

    response = Client().post(
        "/api/accounts/login/",
        {"username": "alice", "password": "s3cret-pw"},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content


@pytest.mark.django_db
def test_throttle_buckets_on_the_last_forwarded_address(client, django_user_model, settings):
    # NUM_PROXIES=1 (the production value) means DRF counts X-Forwarded-For's
    # last entry -- the one this deployment's own proxy appended. Whatever the
    # client prepended must not open a second bucket.
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "NUM_PROXIES": 1}
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")

    for i in range(10):
        response = client.post(
            "/api/accounts/login/",
            {"username": "alice", "password": "wrong"},
            content_type="application/json",
            HTTP_X_FORWARDED_FOR=f"10.0.0.{i}, 203.0.113.5",
        )
        assert response.status_code == 400

    spoofed = client.post(
        "/api/accounts/login/",
        {"username": "alice", "password": "s3cret-pw"},
        content_type="application/json",
        HTTP_X_FORWARDED_FOR="10.0.0.99, 203.0.113.5",
    )
    assert spoofed.status_code == 429

    # A genuinely different client -- different last entry -- keeps its own budget.
    other = client.post(
        "/api/accounts/login/",
        {"username": "alice", "password": "s3cret-pw"},
        content_type="application/json",
        HTTP_X_FORWARDED_FOR="10.0.0.99, 203.0.113.6",
    )
    assert other.status_code == 200
