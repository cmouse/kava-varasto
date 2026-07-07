from datetime import date, timedelta

import pytest

from kava_varasto.inventory.models import Category, Equipment
from kava_varasto.loans.models import Loan, LoanItem

FUTURE_DUE_DATE = (date.today() + timedelta(days=60)).isoformat()


@pytest.fixture
def equipment(db):
    category = Category.objects.create(name="Cooking")
    return Equipment.objects.create(name="Trangia stove", quantity=5, category=category)


@pytest.mark.django_db
def test_loan_create_requires_auth(client):
    response = client.post("/api/loans/", {}, content_type="application/json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_loan_create_sets_responsible_and_echoes_items(admin_client, admin_user, equipment):
    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Matti Meikäläinen",
            "borrower_phone": "0401234567",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 2}],
        },
        content_type="application/json",
    )

    assert response.status_code == 201, response.json()
    loan = Loan.objects.get()
    assert loan.responsible == admin_user
    assert loan.items.count() == 1
    data = response.json()
    assert data["items"][0]["quantity"] == 2
    assert data["responsible"] == admin_user.username


@pytest.mark.django_db
def test_loan_create_requires_at_least_one_item(admin_client, equipment):
    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Matti",
            "borrower_phone": "0401234567",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [],
        },
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_loan_create_rejects_duplicate_equipment(admin_client, equipment):
    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Matti",
            "borrower_phone": "0401234567",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [
                {"equipment": equipment.pk, "quantity": 1},
                {"equipment": equipment.pk, "quantity": 1},
            ],
        },
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_loan_create_rejects_quantity_over_available(admin_client, equipment):
    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Matti",
            "borrower_phone": "0401234567",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 6}],
        },
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_loan_create_rejects_single_word_name(admin_client, equipment):
    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Matti",
            "borrower_phone": "0401234567",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 1}],
        },
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "borrower_name" in response.json()


@pytest.mark.django_db
def test_loan_create_rejects_invalid_phone(admin_client, equipment):
    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Matti Meikäläinen",
            "borrower_phone": "12345",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 1}],
        },
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "borrower_phone" in response.json()


@pytest.mark.django_db
def test_loan_create_accepts_plus358_phone(admin_client, equipment):
    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Matti Meikäläinen",
            "borrower_phone": "+358401234567",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 1}],
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.json()


@pytest.mark.django_db
def test_loan_create_rejects_past_due_date(admin_client, equipment):
    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Matti Meikäläinen",
            "borrower_phone": "0401234567",
            "due_date": "2020-01-01",
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 1}],
        },
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "due_date" in response.json()


@pytest.mark.django_db
def test_loan_create_accounts_for_stock_already_out_on_other_loans(admin_client, admin_user, equipment):
    first_loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    LoanItem.objects.create(loan=first_loan, equipment=equipment, quantity=3)

    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Liisa Virtanen",
            "borrower_phone": "0407654321",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 2}],
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.json()

    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Kalle",
            "borrower_phone": "0409876543",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 1}],
        },
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_loan_create_allows_stock_freed_by_a_return(admin_client, admin_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    item = LoanItem.objects.create(loan=loan, equipment=equipment, quantity=5)

    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Liisa",
            "borrower_phone": "0407654321",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 1}],
        },
        content_type="application/json",
    )
    assert response.status_code == 400

    item.quantity_returned = 2
    item.save()

    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Liisa Virtanen",
            "borrower_phone": "0407654321",
            "due_date": FUTURE_DUE_DATE,
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 2}],
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.json()


@pytest.mark.django_db
def test_loan_list_requires_auth(client):
    response = client.get("/api/loans/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_loan_list_reports_active_and_returned(admin_client, admin_user, equipment):
    active_loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    LoanItem.objects.create(loan=active_loan, equipment=equipment, quantity=2)

    returned_loan = Loan.objects.create(
        borrower_name="Liisa", borrower_phone="0407654321", due_date="2026-07-01", responsible=admin_user
    )
    item = LoanItem.objects.create(loan=returned_loan, equipment=equipment, quantity=1)
    item.quantity_returned = 1
    item.save()
    returned_loan.mark_returned_if_complete(admin_user)

    response = admin_client.get("/api/loans/")

    assert response.status_code == 200
    data = response.json()
    by_borrower = {loan["borrower_name"]: loan for loan in data}
    assert by_borrower["Matti"]["is_returned"] is False
    assert by_borrower["Liisa"]["is_returned"] is True
    assert by_borrower["Liisa"]["returned_by"] == admin_user.username


@pytest.mark.django_db
def test_loanable_equipment_requires_auth(client):
    response = client.get("/api/loans/loanable-equipment/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_loanable_equipment_reflects_stock_already_out(admin_client, admin_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    LoanItem.objects.create(loan=loan, equipment=equipment, quantity=2)

    response = admin_client.get("/api/loans/loanable-equipment/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["loanable_quantity"] == 3
    assert data[0]["quantity"] == 5
    assert data[0]["is_external_loanable"] is False


@pytest.mark.django_db
def test_loan_return_requires_auth(client, admin_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    item = LoanItem.objects.create(loan=loan, equipment=equipment, quantity=2)

    response = client.post(
        f"/api/loans/{loan.pk}/return/",
        {"items": [{"item": item.pk, "quantity_returned": 2}]},
        content_type="application/json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_loan_return_full_marks_loan_returned(admin_client, admin_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    item = LoanItem.objects.create(loan=loan, equipment=equipment, quantity=2)

    response = admin_client.post(
        f"/api/loans/{loan.pk}/return/",
        {"items": [{"item": item.pk, "quantity_returned": 2}]},
        content_type="application/json",
    )

    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["is_returned"] is True
    assert data["returned_by"] == admin_user.username
    assert data["returned_at"] is not None
    assert data["items"][0]["quantity_returned"] == 2

    loan.refresh_from_db()
    assert loan.is_returned is True


@pytest.mark.django_db
def test_loan_return_partial_keeps_loan_active(admin_client, admin_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    item_a = LoanItem.objects.create(loan=loan, equipment=equipment, quantity=2)
    category = item_a.equipment.category
    other_equipment = Equipment.objects.create(name="Lantern", quantity=1, category=category)
    item_b = LoanItem.objects.create(loan=loan, equipment=other_equipment, quantity=1)

    response = admin_client.post(
        f"/api/loans/{loan.pk}/return/",
        {"items": [{"item": item_a.pk, "quantity_returned": 2}]},
        content_type="application/json",
    )

    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["is_returned"] is False
    by_item_id = {entry["id"]: entry for entry in data["items"]}
    assert by_item_id[item_a.pk]["quantity_returned"] == 2
    assert by_item_id[item_b.pk]["quantity_returned"] == 0

    response = admin_client.post(
        f"/api/loans/{loan.pk}/return/",
        {"items": [{"item": item_b.pk, "quantity_returned": 1}]},
        content_type="application/json",
    )
    assert response.status_code == 200, response.json()
    assert response.json()["is_returned"] is True


@pytest.mark.django_db
def test_loan_return_rejects_decreasing_quantity(admin_client, admin_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    item = LoanItem.objects.create(loan=loan, equipment=equipment, quantity=2, quantity_returned=1)

    response = admin_client.post(
        f"/api/loans/{loan.pk}/return/",
        {"items": [{"item": item.pk, "quantity_returned": 0}]},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_loan_return_rejects_quantity_over_borrowed(admin_client, admin_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    item = LoanItem.objects.create(loan=loan, equipment=equipment, quantity=2)

    response = admin_client.post(
        f"/api/loans/{loan.pk}/return/",
        {"items": [{"item": item.pk, "quantity_returned": 3}]},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_loan_return_rejects_item_from_another_loan(admin_client, admin_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    other_loan = Loan.objects.create(
        borrower_name="Liisa", borrower_phone="0407654321", due_date="2026-08-01", responsible=admin_user
    )
    other_item = LoanItem.objects.create(loan=other_loan, equipment=equipment, quantity=1)

    response = admin_client.post(
        f"/api/loans/{loan.pk}/return/",
        {"items": [{"item": other_item.pk, "quantity_returned": 1}]},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_loan_return_rejects_already_returned_loan(admin_client, admin_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    item = LoanItem.objects.create(loan=loan, equipment=equipment, quantity=2, quantity_returned=2)
    loan.mark_returned_if_complete(admin_user)

    response = admin_client.post(
        f"/api/loans/{loan.pk}/return/",
        {"items": [{"item": item.pk, "quantity_returned": 2}]},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_loan_return_frees_stock_for_new_loan(admin_client, admin_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    item = LoanItem.objects.create(loan=loan, equipment=equipment, quantity=5)

    response = admin_client.get("/api/loans/loanable-equipment/")
    assert response.json()[0]["loanable_quantity"] == 0

    response = admin_client.post(
        f"/api/loans/{loan.pk}/return/",
        {"items": [{"item": item.pk, "quantity_returned": 5}]},
        content_type="application/json",
    )
    assert response.status_code == 200, response.json()

    response = admin_client.get("/api/loans/loanable-equipment/")
    assert response.json()[0]["loanable_quantity"] == 5
