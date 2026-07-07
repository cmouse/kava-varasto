from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Category, Equipment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = [
        "short_code",
        "name",
        "category",
        "quantity",
        "broken_quantity",
        "available_quantity",
        "is_external_loanable",
    ]
    list_filter = ["category", "is_external_loanable"]
    search_fields = ["name", "short_code"]
    list_editable = ["broken_quantity"]

    @admin.display(description=_("available quantity"))
    def available_quantity(self, obj):
        return obj.available_quantity
