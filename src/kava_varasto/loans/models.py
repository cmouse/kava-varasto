import re

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from kava_varasto.inventory.models import Equipment

PHONE_RE = re.compile(r"^(\+358\d{6,12}|0\d{6,12})$")


class Loan(models.Model):
    borrower_name = models.CharField(_("borrower name"), max_length=200)
    borrower_phone = models.CharField(
        _("borrower phone"),
        max_length=30,
        validators=[
            RegexValidator(
                PHONE_RE,
                _("Enter a valid phone number, e.g. 0401234567 or +358401234567."),
            )
        ],
    )
    due_date = models.DateField(_("due date"))
    details = models.TextField(_("details"), blank=True)
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loans_given",
        verbose_name=_("responsible"),
        help_text=_("Staff member who handed out this loan."),
    )
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loans_returned",
        verbose_name=_("returned by"),
        null=True,
        blank=True,
        help_text=_("Staff member who processed the return. Set automatically once all equipment is returned."),
    )
    returned_at = models.DateTimeField(_("returned at"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("loan")
        verbose_name_plural = _("loans")
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(borrower_name__contains=" "),
                name="loan_borrower_name_has_space",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(returned_at__isnull=True, returned_by__isnull=True)
                    | models.Q(returned_at__isnull=False, returned_by__isnull=False)
                ),
                name="loan_returned_fields_consistent",
            ),
        ]

    def __str__(self):
        return f"{self.borrower_name} ({self.due_date})"

    def clean(self):
        super().clean()
        # Strict superset of the loan_borrower_name_has_space constraint so
        # bad input fails as ValidationError, not IntegrityError.
        if " " not in self.borrower_name or len(self.borrower_name.split()) < 2:
            raise ValidationError({"borrower_name": _("Enter both first and last name.")})
        if self._state.adding and self.due_date and self.due_date < timezone.localdate():
            raise ValidationError({"due_date": _("Due date cannot be in the past.")})
        if (self.returned_at is None) != (self.returned_by is None):
            raise ValidationError({"returned_by": _("Returned-at and returned-by must be set together.")})

    @property
    def is_returned(self):
        return self.returned_at is not None

    @property
    def is_fully_returned(self):
        items = list(self.items.all())
        return bool(items) and all(item.is_fully_returned for item in items)

    def mark_returned_if_complete(self, by_user):
        """Archive the loan once every item on it has been fully returned."""
        if self.is_returned or not self.is_fully_returned:
            return False
        self.returned_at = timezone.now()
        self.returned_by = by_user
        self.save(update_fields=["returned_at", "returned_by"])
        return True

    def delete(self, *args, **kwargs):
        raise PermissionDenied(_("Loans cannot be deleted once created."))


class LoanItem(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="items", verbose_name=_("loan"))
    equipment = models.ForeignKey(
        Equipment, on_delete=models.PROTECT, related_name="loan_items", verbose_name=_("equipment")
    )
    quantity = models.PositiveIntegerField(_("quantity"), validators=[MinValueValidator(1)])
    quantity_returned = models.PositiveIntegerField(_("quantity returned"), default=0)
    quantity_broken = models.PositiveIntegerField(
        _("quantity broken"),
        default=0,
        help_text=_("How many of the returned quantity came back broken."),
    )

    class Meta:
        verbose_name = _("loan item")
        verbose_name_plural = _("loan items")
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name="loanitem_quantity_gte_one"),
            models.CheckConstraint(
                condition=models.Q(quantity_returned__lte=models.F("quantity")),
                name="loanitem_quantity_returned_lte_quantity",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_broken__lte=models.F("quantity_returned")),
                name="loanitem_quantity_broken_lte_quantity_returned",
            ),
            models.UniqueConstraint(fields=["loan", "equipment"], name="loanitem_unique_loan_equipment"),
        ]

    def __str__(self):
        return f"{self.equipment} x{self.quantity}"

    @property
    def is_fully_returned(self):
        return self.quantity_returned >= self.quantity

    def clean(self):
        super().clean()
        if self.quantity_returned > self.quantity:
            raise ValidationError({"quantity_returned": _("Returned quantity cannot exceed borrowed quantity.")})
        if self.quantity_broken > self.quantity_returned:
            raise ValidationError({"quantity_broken": _("Broken quantity cannot exceed returned quantity.")})
