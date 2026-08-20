import pytest
from django.urls import reverse

from kava_varasto.accounts.models import User
from kava_varasto.repairs.models import RepairTicket, TicketStatus


@pytest.mark.django_db
def test_admin_add_stamps_the_reporter(admin_client, admin_user):
    response = admin_client.post(
        reverse("admin:repairs_repairticket_add"),
        {"title": "Sharpen all them axes", "description": "", "status": TicketStatus.OPEN, "equipment": []},
    )

    assert response.status_code == 302
    ticket = RepairTicket.objects.get()
    assert ticket.reported_by == admin_user
    assert ticket.resolved_at is None


@pytest.mark.django_db
def test_admin_can_close_a_ticket(admin_client, admin_user):
    reporter = User.objects.create_user(username="reporter", password="password")
    ticket = RepairTicket.objects.create(title="Bent pole", reported_by=reporter)

    response = admin_client.post(
        reverse("admin:repairs_repairticket_change", args=[ticket.pk]),
        {"title": ticket.title, "description": "", "status": TicketStatus.DONE, "equipment": []},
    )

    assert response.status_code == 302
    ticket.refresh_from_db()
    assert ticket.status == TicketStatus.DONE
    assert ticket.resolved_by == admin_user
    assert ticket.resolved_at is not None


@pytest.mark.django_db
def test_admin_can_reopen_a_ticket(admin_client, admin_user):
    ticket = RepairTicket.objects.create(title="Bent pole", reported_by=admin_user)
    ticket.set_status(TicketStatus.DONE, admin_user)
    ticket.save()

    response = admin_client.post(
        reverse("admin:repairs_repairticket_change", args=[ticket.pk]),
        {"title": ticket.title, "description": "", "status": TicketStatus.OPEN, "equipment": []},
    )

    assert response.status_code == 302
    ticket.refresh_from_db()
    assert ticket.status == TicketStatus.OPEN
    assert ticket.resolved_by is None
    assert ticket.resolved_at is None


@pytest.mark.django_db
def test_admin_add_can_start_closed(admin_client, admin_user):
    """Filing something already dealt with must stamp, not trip the constraint."""
    response = admin_client.post(
        reverse("admin:repairs_repairticket_add"),
        {"title": "Axe sharpened at camp", "description": "", "status": TicketStatus.DONE, "equipment": []},
    )

    assert response.status_code == 302
    ticket = RepairTicket.objects.get()
    assert ticket.status == TicketStatus.DONE
    assert ticket.reported_by == admin_user
    assert ticket.resolved_by == admin_user
    assert ticket.resolved_at is not None
