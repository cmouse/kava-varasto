import pytest

from kava_varasto.accounts.models import User
from kava_varasto.inventory.models import Category, Equipment, StorageLocation
from kava_varasto.repairs.models import RepairTicket, TicketStatus


@pytest.fixture
def axe(db):
    category = Category.objects.create(name="Tools")
    location = StorageLocation.objects.get(name="Kolo")
    return Equipment.objects.create(
        name="Axe", quantity=6, broken_quantity=1, category=category, location=location
    )


@pytest.mark.django_db
def test_ticket_list_requires_auth(client):
    assert client.get("/api/repairs/").status_code == 403


@pytest.mark.django_db
def test_create_stamps_the_reporter(admin_client, admin_user):
    response = admin_client.post(
        "/api/repairs/", {"title": "Sharpen all them axes"}, content_type="application/json"
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Sharpen all them axes"
    assert data["status"] == TicketStatus.OPEN
    assert data["is_open"] is True
    assert data["reported_by"] == str(admin_user)
    assert data["resolved_by"] is None
    assert data["equipment"] == []


@pytest.mark.django_db
def test_create_with_tagged_equipment(admin_client, axe):
    response = admin_client.post(
        "/api/repairs/",
        {"title": "Sharpen all them axes", "description": "Blunt", "equipment": [axe.pk]},
        content_type="application/json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["equipment"] == [{"id": axe.pk, "name": "Axe", "short_code": None}]
    assert data["description"] == "Blunt"


@pytest.mark.django_db
def test_create_rejects_a_blank_title(admin_client):
    response = admin_client.post("/api/repairs/", {"title": "   "}, content_type="application/json")

    assert response.status_code == 400
    assert "title" in response.json()


@pytest.mark.django_db
def test_list_hides_closed_tickets_by_default(admin_client, admin_user):
    RepairTicket.objects.create(title="Bent pole", reported_by=admin_user)
    closed = RepairTicket.objects.create(title="Torn tent", reported_by=admin_user)
    closed.set_status(TicketStatus.DONE, admin_user)
    closed.save()

    titles = [item["title"] for item in admin_client.get("/api/repairs/").json()]
    assert titles == ["Bent pole"]

    all_titles = {item["title"] for item in admin_client.get("/api/repairs/?status=all").json()}
    assert all_titles == {"Bent pole", "Torn tent"}

    done_titles = [item["title"] for item in admin_client.get("/api/repairs/?status=done").json()]
    assert done_titles == ["Torn tent"]


@pytest.mark.django_db
def test_list_rejects_an_unknown_status(admin_client):
    response = admin_client.get("/api/repairs/?status=don")

    assert response.status_code == 400
    assert "status" in response.json()


@pytest.mark.django_db
def test_patch_to_done_stamps_the_resolver(admin_client, admin_user):
    reporter = User.objects.create_user(username="reporter", password="password")
    ticket = RepairTicket.objects.create(title="Bent pole", reported_by=reporter)

    response = admin_client.patch(
        f"/api/repairs/{ticket.pk}/", {"status": TicketStatus.DONE}, content_type="application/json"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == TicketStatus.DONE
    assert data["is_open"] is False
    assert data["resolved_by"] == str(admin_user)
    assert data["resolved_at"] is not None
    assert data["reported_by"] == str(reporter)


@pytest.mark.django_db
def test_second_patch_to_done_keeps_the_original_resolver(admin_client, admin_user):
    resolver = User.objects.create_user(username="resolver", password="password")
    ticket = RepairTicket.objects.create(title="Bent pole", reported_by=admin_user)
    ticket.set_status(TicketStatus.DONE, resolver)
    ticket.save()

    response = admin_client.patch(
        f"/api/repairs/{ticket.pk}/", {"status": TicketStatus.DONE}, content_type="application/json"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["resolved_by"] == str(resolver)
    stamped_at = ticket.resolved_at
    ticket.refresh_from_db()
    assert ticket.resolved_at == stamped_at


@pytest.mark.django_db
def test_patch_back_to_open_clears_the_resolution(admin_client, admin_user):
    ticket = RepairTicket.objects.create(title="Bent pole", reported_by=admin_user)
    ticket.set_status(TicketStatus.DONE, admin_user)
    ticket.save()

    response = admin_client.patch(
        f"/api/repairs/{ticket.pk}/", {"status": TicketStatus.OPEN}, content_type="application/json"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["resolved_by"] is None
    assert data["resolved_at"] is None


@pytest.mark.django_db
def test_patch_replaces_the_tagged_equipment(admin_client, admin_user, axe):
    other = Equipment.objects.create(
        name="Hatchet", quantity=2, category=axe.category, location=axe.location
    )
    ticket = RepairTicket.objects.create(title="Sharpen all them axes", reported_by=admin_user)
    ticket.equipment.set([axe])

    response = admin_client.patch(
        f"/api/repairs/{ticket.pk}/", {"equipment": [other.pk]}, content_type="application/json"
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["equipment"]] == [other.pk]


@pytest.mark.django_db
def test_ticket_can_be_deleted(admin_client, admin_user):
    ticket = RepairTicket.objects.create(title="Typo", reported_by=admin_user)

    assert admin_client.delete(f"/api/repairs/{ticket.pk}/").status_code == 204
    assert not RepairTicket.objects.exists()


@pytest.mark.django_db
def test_tickets_never_touch_broken_quantity(admin_client, admin_user, axe):
    """The queue records the work; Equipment.broken_quantity stays admin-owned."""
    response = admin_client.post(
        "/api/repairs/",
        {"title": "Axe head loose", "equipment": [axe.pk]},
        content_type="application/json",
    )
    assert response.status_code == 201
    axe.refresh_from_db()
    assert axe.broken_quantity == 1

    ticket_id = response.json()["id"]
    admin_client.patch(
        f"/api/repairs/{ticket_id}/", {"status": TicketStatus.DONE}, content_type="application/json"
    )

    axe.refresh_from_db()
    assert axe.broken_quantity == 1
