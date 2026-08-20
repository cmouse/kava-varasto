import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from kava_varasto.accounts.models import User
from kava_varasto.inventory.models import Category, Equipment, StorageLocation
from kava_varasto.repairs.models import RepairTicket, TicketStatus


@pytest.fixture
def reporter(db):
    return User.objects.create_user(username="reporter", password="password")


@pytest.fixture
def resolver(db):
    return User.objects.create_user(username="resolver", password="password")


@pytest.fixture
def axe(db):
    category = Category.objects.create(name="Tools")
    location = StorageLocation.objects.get(name="Kolo")
    return Equipment.objects.create(name="Axe", quantity=6, category=category, location=location)


@pytest.mark.django_db
def test_ticket_str_is_the_title(reporter):
    ticket = RepairTicket.objects.create(title="Sharpen all them axes", reported_by=reporter)
    assert str(ticket) == "Sharpen all them axes"


@pytest.mark.django_db
def test_ticket_without_equipment_is_valid(reporter):
    ticket = RepairTicket.objects.create(title="Service the trailer", reported_by=reporter)
    ticket.full_clean()
    assert list(ticket.equipment.all()) == []


@pytest.mark.django_db
def test_ticket_tags_several_equipment(reporter, axe):
    other = Equipment.objects.create(
        name="Hatchet", quantity=2, category=axe.category, location=axe.location
    )
    ticket = RepairTicket.objects.create(title="Sharpen all them axes", reported_by=reporter)
    ticket.equipment.set([axe, other])
    assert ticket.equipment.count() == 2
    assert list(axe.repair_tickets.all()) == [ticket]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status,expected",
    [
        (TicketStatus.OPEN, True),
        (TicketStatus.IN_PROGRESS, True),
        (TicketStatus.DONE, False),
        (TicketStatus.WONTFIX, False),
    ],
)
def test_is_open(reporter, status, expected):
    ticket = RepairTicket(title="Bent pole", reported_by=reporter, status=status)
    assert ticket.is_open is expected


@pytest.mark.django_db
def test_closed_ticket_without_resolution_is_rejected(reporter):
    with pytest.raises(IntegrityError):
        RepairTicket.objects.create(title="Bent pole", reported_by=reporter, status=TicketStatus.DONE)


@pytest.mark.django_db
def test_open_ticket_with_resolution_is_rejected(reporter, resolver):
    with pytest.raises(IntegrityError):
        RepairTicket.objects.create(
            title="Bent pole",
            reported_by=reporter,
            status=TicketStatus.OPEN,
            resolved_at=timezone.now(),
            resolved_by=resolver,
        )


@pytest.mark.django_db
def test_resolution_fields_must_be_set_together(reporter):
    with pytest.raises(IntegrityError):
        RepairTicket.objects.create(
            title="Bent pole",
            reported_by=reporter,
            status=TicketStatus.DONE,
            resolved_at=timezone.now(),
        )


@pytest.mark.django_db
def test_clean_mirrors_the_resolution_constraint(reporter, resolver):
    ticket = RepairTicket(title="Bent pole", reported_by=reporter, status=TicketStatus.DONE)
    with pytest.raises(ValidationError) as excinfo:
        ticket.full_clean()
    assert "status" in excinfo.value.error_dict

    ticket.resolved_at = timezone.now()
    with pytest.raises(ValidationError) as excinfo:
        ticket.full_clean()
    assert "resolved_by" in excinfo.value.error_dict

    ticket.resolved_by = resolver
    ticket.full_clean()


@pytest.mark.django_db
def test_set_status_stamps_the_resolver(reporter, resolver):
    ticket = RepairTicket.objects.create(title="Bent pole", reported_by=reporter)

    assert ticket.set_status(TicketStatus.DONE, resolver) is True
    ticket.save()

    ticket.refresh_from_db()
    assert ticket.resolved_by == resolver
    assert ticket.resolved_at is not None


@pytest.mark.django_db
def test_set_status_to_the_same_status_keeps_the_original_resolver(reporter, resolver):
    ticket = RepairTicket.objects.create(title="Bent pole", reported_by=reporter)
    ticket.set_status(TicketStatus.DONE, resolver)
    ticket.save()
    first_resolved_at = ticket.resolved_at

    assert ticket.set_status(TicketStatus.DONE, reporter) is False
    ticket.save()

    ticket.refresh_from_db()
    assert ticket.resolved_by == resolver
    assert ticket.resolved_at == first_resolved_at


@pytest.mark.django_db
def test_set_status_clears_the_resolution_on_reopen(reporter, resolver):
    ticket = RepairTicket.objects.create(title="Bent pole", reported_by=reporter)
    ticket.set_status(TicketStatus.DONE, resolver)
    ticket.save()

    ticket.set_status(TicketStatus.OPEN, reporter)
    ticket.save()

    ticket.refresh_from_db()
    assert ticket.resolved_by is None
    assert ticket.resolved_at is None


@pytest.mark.django_db
def test_in_progress_stays_open(reporter, resolver):
    ticket = RepairTicket.objects.create(title="Bent pole", reported_by=reporter)

    ticket.set_status(TicketStatus.IN_PROGRESS, resolver)
    ticket.save()

    ticket.refresh_from_db()
    assert ticket.is_open
    assert ticket.resolved_at is None
