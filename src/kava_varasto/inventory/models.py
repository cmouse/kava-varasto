from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(_("name"), max_length=100, unique=True)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class EquipmentImage(models.Model):
    name = models.CharField(_("name"), max_length=100)
    image = models.ImageField(_("image"), upload_to="equipment/")
    uploaded_at = models.DateTimeField(_("uploaded at"), auto_now_add=True)

    class Meta:
        verbose_name = _("equipment image")
        verbose_name_plural = _("equipment images")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Equipment(models.Model):
    name = models.CharField(_("name"), max_length=200)
    # Most equipment has a short code (e.g. X75, M96); some doesn't. null=True
    # (rather than just blank) so multiple blank entries don't collide with
    # the unique constraint -- SQL NULLs are never equal to each other.
    short_code = models.CharField(
        _("short code"),
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text=_("Identifies one specific physical item, e.g. X75. Leave blank for "
                     "equipment tracked only as a stock count (see quantity)."),
    )
    # Meaningful only when short_code is blank: a short code identifies one
    # specific physical item, so that item's quantity is always 1. Equipment
    # with no code (e.g. "Trangia stove") is tracked as a stock count instead.
    quantity = models.PositiveIntegerField(
        _("quantity"),
        default=1,
        help_text=_("Total number in stock. Must be 1 for equipment with a short code."),
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="equipment", verbose_name=_("category")
    )
    is_external_loanable = models.BooleanField(
        _("external loanable"),
        default=False,
        help_text=_("If unset, only club members can borrow this equipment."),
    )
    broken_quantity = models.PositiveIntegerField(
        _("broken quantity"),
        default=0,
        help_text=_("How many of this equipment are currently broken and unavailable for loan."),
    )
    # Shared FK so one uploaded photo can be reused by several equipment
    # entries (e.g. ten identical stoves).
    image = models.ForeignKey(
        EquipmentImage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipment",
        verbose_name=_("image"),
        help_text=_("Optional photo shown in the storage detail view."),
    )

    class Meta:
        verbose_name = _("equipment")
        verbose_name_plural = _("equipment")
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(short_code__isnull=True) | models.Q(quantity=1),
                name="equipment_short_code_implies_quantity_one",
            ),
            models.CheckConstraint(
                condition=models.Q(broken_quantity__lte=models.F("quantity")),
                name="equipment_broken_quantity_lte_quantity",
            ),
        ]

    def __str__(self):
        return f"{self.short_code} {self.name}" if self.short_code else self.name

    @property
    def available_quantity(self):
        return self.quantity - self.broken_quantity

    def clean(self):
        super().clean()
        if self.short_code and self.quantity != 1:
            raise ValidationError(
                {"quantity": _("Equipment with a short code identifies a single item, so quantity must be 1.")}
            )
        if self.broken_quantity > self.quantity:
            raise ValidationError(
                {"broken_quantity": _("Broken quantity cannot exceed total quantity.")}
            )
