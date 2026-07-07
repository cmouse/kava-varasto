import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError

from kava_varasto.accounts.models import User
from kava_varasto.inventory.models import Category, Equipment
from kava_varasto.loans.models import Loan, LoanItem


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(username="staff", password="password")


@pytest.fixture
def equipment(db):
    category = Category.objects.create(name="Cooking")
    return Equipment.objects.create(name="Trangia stove", quantity=5, category=category)


@pytest.mark.django_db
def test_loan_str(staff_user):
    loan = Loan.objects.create(
        borrower_name="Matti Meikäläinen",
        borrower_phone="0401234567",
        due_date="2026-08-01",
        responsible=staff_user,
    )
    assert str(loan) == "Matti Meikäläinen (2026-08-01)"


@pytest.mark.django_db
def test_loan_is_returned_false_by_default(staff_user):
    loan = Loan.objects.create(
        borrower_name="Matti",
        borrower_phone="0401234567",
        due_date="2026-08-01",
        responsible=staff_user,
    )
    assert loan.is_returned is False


@pytest.mark.django_db
def test_loan_is_fully_returned_false_with_no_items(staff_user):
    loan = Loan.objects.create(
        borrower_name="Matti",
        borrower_phone="0401234567",
        due_date="2026-08-01",
        responsible=staff_user,
    )
    assert loan.is_fully_returned is False


@pytest.mark.django_db
def test_loan_mark_returned_if_complete_noop_when_partially_returned(staff_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti",
        borrower_phone="0401234567",
        due_date="2026-08-01",
        responsible=staff_user,
    )
    LoanItem.objects.create(loan=loan, equipment=equipment, quantity=2, quantity_returned=1)

    assert loan.mark_returned_if_complete(staff_user) is False
    assert loan.is_returned is False


@pytest.mark.django_db
def test_loan_mark_returned_if_complete_marks_loan_returned(staff_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti",
        borrower_phone="0401234567",
        due_date="2026-08-01",
        responsible=staff_user,
    )
    LoanItem.objects.create(loan=loan, equipment=equipment, quantity=2, quantity_returned=2)

    assert loan.mark_returned_if_complete(staff_user) is True
    assert loan.is_returned is True
    assert loan.returned_by == staff_user
    assert loan.returned_at is not None


@pytest.mark.django_db
def test_loan_delete_is_forbidden(staff_user):
    loan = Loan.objects.create(
        borrower_name="Matti",
        borrower_phone="0401234567",
        due_date="2026-08-01",
        responsible=staff_user,
    )
    with pytest.raises(PermissionDenied):
        loan.delete()


@pytest.mark.django_db
def test_loanitem_quantity_returned_over_quantity_rejected_by_clean(staff_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti",
        borrower_phone="0401234567",
        due_date="2026-08-01",
        responsible=staff_user,
    )
    item = LoanItem(loan=loan, equipment=equipment, quantity=2, quantity_returned=3)
    with pytest.raises(ValidationError):
        item.full_clean()


@pytest.mark.django_db
def test_loanitem_quantity_returned_over_quantity_rejected_by_db_constraint(staff_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti",
        borrower_phone="0401234567",
        due_date="2026-08-01",
        responsible=staff_user,
    )
    with pytest.raises(IntegrityError):
        LoanItem.objects.create(loan=loan, equipment=equipment, quantity=2, quantity_returned=3)


@pytest.mark.django_db
def test_loanitem_duplicate_equipment_on_same_loan_rejected(staff_user, equipment):
    loan = Loan.objects.create(
        borrower_name="Matti",
        borrower_phone="0401234567",
        due_date="2026-08-01",
        responsible=staff_user,
    )
    LoanItem.objects.create(loan=loan, equipment=equipment, quantity=1)
    with pytest.raises(IntegrityError):
        LoanItem.objects.create(loan=loan, equipment=equipment, quantity=1)
