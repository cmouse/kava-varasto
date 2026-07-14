from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Category, Equipment, EquipmentImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(EquipmentImage)
class EquipmentImageAdmin(admin.ModelAdmin):
    list_display = ["name", "thumbnail", "uploaded_at"]
    search_fields = ["name"]
    readonly_fields = ["uploaded_at"]

    @admin.display(description=_("preview"))
    def thumbnail(self, obj):
        if not obj.image:
            return ""
        return format_html('<img src="{}" style="max-height: 60px">', obj.image.url)


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
