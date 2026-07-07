import pytest

from kava_varasto.inventory.models import Category, Equipment
from kava_varasto.loans.models import Loan, LoanItem


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
            "borrower_name": "Matti",
            "borrower_phone": "0401234567",
            "due_date": "2026-08-01",
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
            "due_date": "2026-08-01",
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
            "due_date": "2026-08-01",
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
            "due_date": "2026-08-01",
            "details": "",
            "items": [{"equipment": equipment.pk, "quantity": 6}],
        },
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_loan_create_accounts_for_stock_already_out_on_other_loans(admin_client, admin_user, equipment):
    first_loan = Loan.objects.create(
        borrower_name="Matti", borrower_phone="0401234567", due_date="2026-08-01", responsible=admin_user
    )
    LoanItem.objects.create(loan=first_loan, equipment=equipment, quantity=3)

    response = admin_client.post(
        "/api/loans/",
        {
            "borrower_name": "Liisa",
            "borrower_phone": "0407654321",
            "due_date": "2026-08-01",
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
            "due_date": "2026-08-01",
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
            "due_date": "2026-08-01",
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
            "borrower_name": "Liisa",
            "borrower_phone": "0407654321",
            "due_date": "2026-08-01",
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
