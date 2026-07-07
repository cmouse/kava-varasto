from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Equipment(models.Model):
    name = models.CharField(max_length=200)
    # Most equipment has a short code (e.g. X75, M96); some doesn't. null=True
    # (rather than just blank) so multiple blank entries don't collide with
    # the unique constraint -- SQL NULLs are never equal to each other.
    short_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="equipment")
    is_external_loanable = models.BooleanField(
        default=False,
        help_text="If unset, only club members can borrow this equipment.",
    )

    class Meta:
        verbose_name_plural = "equipment"
        ordering = ["name"]

    def __str__(self):
        return f"{self.short_code} {self.name}" if self.short_code else self.name
