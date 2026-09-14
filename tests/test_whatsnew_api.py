import pytest

from kava_varasto.whatsnew import WHATS_NEW, is_unseen


@pytest.mark.django_db
def test_whats_new_requires_authentication(client):
    response = client.get("/api/accounts/whats-new/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_whats_new_get_returns_current_version_and_entries(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    response = client.get("/api/accounts/whats-new/")

    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["current_version"] == WHATS_NEW[0]["version"]
    assert [entry["version"] for entry in data["entries"]] == [entry["version"] for entry in WHATS_NEW]


@pytest.mark.django_db
def test_whats_new_get_reports_unseen_for_a_fresh_user(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    response = client.get("/api/accounts/whats-new/")

    assert response.json()["unseen"] is True


@pytest.mark.django_db
def test_whats_new_get_does_not_stamp_seen_version(client, django_user_model):
    user = django_user_model.objects.create_user(username="alice", password="s3cret-pw")
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    client.get("/api/accounts/whats-new/")

    user.refresh_from_db()
    assert user.whats_new_seen_version == ""


@pytest.mark.django_db
def test_whats_new_post_stamps_current_version_and_returns_updated_user(client, django_user_model):
    user = django_user_model.objects.create_user(username="alice", password="s3cret-pw")
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    response = client.post("/api/accounts/whats-new/", content_type="application/json")

    assert response.status_code == 200, response.json()
    assert response.json()["authenticated"] is True
    assert response.json()["user"]["whats_new_seen_version"] == WHATS_NEW[0]["version"]
    user.refresh_from_db()
    assert user.whats_new_seen_version == WHATS_NEW[0]["version"]


@pytest.mark.django_db
def test_whats_new_get_reports_seen_after_ack(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw")
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )
    client.post("/api/accounts/whats-new/", content_type="application/json")

    response = client.get("/api/accounts/whats-new/")

    assert response.json()["unseen"] is False


@pytest.mark.django_db
def test_whats_new_refused_while_password_change_required(client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="s3cret-pw", must_change_password=True)
    client.post(
        "/api/accounts/login/", {"username": "alice", "password": "s3cret-pw"}, content_type="application/json"
    )

    assert client.get("/api/accounts/whats-new/").status_code == 403
    assert client.post("/api/accounts/whats-new/", content_type="application/json").status_code == 403


def test_is_unseen_uses_index_position_not_lexical_order():
    # "0.1.9" sorts lexically above "0.1.20" as a string, but it is the
    # *older* entry positionally -- a string compare would wrongly treat it
    # as already-seen-or-newer and stop the dialog from firing.
    entries = [
        {"version": "0.1.20", "changes": ["..."]},
        {"version": "0.1.9", "changes": ["..."]},
    ]

    assert is_unseen("0.1.9", entries=entries, current_version="0.1.20") is True


def test_is_unseen_false_for_current_version_itself():
    assert is_unseen(WHATS_NEW[0]["version"], entries=WHATS_NEW) is False


def test_is_unseen_treats_blank_or_unknown_version_as_unseen():
    assert is_unseen("", entries=WHATS_NEW) is True
    assert is_unseen("not-a-real-version", entries=WHATS_NEW) is True
