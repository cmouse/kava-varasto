from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from kava_varasto.inventory.models import Equipment


class TicketStatus(models.TextChoices):
    OPEN = "open", _("open")
    IN_PROGRESS = "in_progress", _("in progress")
    DONE = "done", _("done")
    WONTFIX = "wontfix", _("won't fix")


OPEN_STATUSES = (TicketStatus.OPEN, TicketStatus.IN_PROGRESS)
TERMINAL_STATUSES = (TicketStatus.DONE, TicketStatus.WONTFIX)


class RepairTicket(models.Model):
    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    # Optional and many: "X75 pole bent" tags one item, "sharpen all them axes"
    # tags several, and a chore with no particular item ("service the trailer")
    # tags none. The title alone always has to make sense.
    equipment = models.ManyToManyField(
        Equipment,
        blank=True,
        related_name="repair_tickets",
        verbose_name=_("equipment"),
        help_text=_("Which equipment this concerns, if any."),
    )
    status = models.CharField(
        _("status"), max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="repairs_reported",
        verbose_name=_("reported by"),
    )
    reported_at = models.DateTimeField(_("reported at"), auto_now_add=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="repairs_resolved",
        verbose_name=_("resolved by"),
        null=True,
        blank=True,
        help_text=_("Set automatically when the ticket moves to a closed status."),
    )
    resolved_at = models.DateTimeField(_("resolved at"), null=True, blank=True)

    class Meta:
        verbose_name = _("repair ticket")
        verbose_name_plural = _("repair tickets")
        ordering = ["-reported_at"]
        constraints = [
            # The status literals are baked into this constraint's SQL, so
            # adding a fifth status needs a migration that rewrites it -- a
            # TicketStatus edit alone won't do.
            models.CheckConstraint(
                condition=(
                    models.Q(status__in=OPEN_STATUSES, resolved_at__isnull=True, resolved_by__isnull=True)
                    | models.Q(
                        status__in=TERMINAL_STATUSES, resolved_at__isnull=False, resolved_by__isnull=False
                    )
                ),
                name="repairticket_resolution_matches_status",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        return self.status in OPEN_STATUSES

    def clean(self):
        super().clean()
        # Strict mirror of repairticket_resolution_matches_status so bad input
        # fails as ValidationError, not IntegrityError.
        if (self.resolved_at is None) != (self.resolved_by is None):
            raise ValidationError({"resolved_by": _("Resolved-at and resolved-by must be set together.")})
        if self.is_open and self.resolved_at is not None:
            raise ValidationError({"status": _("An open ticket cannot have resolution details.")})
        if not self.is_open and self.resolved_at is None:
            raise ValidationError({"status": _("A closed ticket must record who resolved it and when.")})

    def set_status(self, status, by_user):
        """Move the ticket to `status`, keeping the resolution fields in step.

        The only place that stamps resolved_at/resolved_by. Both the API and
        the admin go through here: the admin change form writes `status`
        directly, and without this the resolution check constraint would
        reject the save with no editable field to satisfy it.
        """
        if status == self.status:
            # Not a transition: leave the original resolver's stamp alone.
            return False
        self.status = status
        if self.is_open:
            self.resolved_at = None
            self.resolved_by = None
        else:
            self.resolved_at = timezone.now()
            self.resolved_by = by_user
        return True
