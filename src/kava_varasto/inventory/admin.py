from django.contrib import admin

from .models import Category, Equipment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ["short_code", "name", "category", "quantity", "is_external_loanable"]
    list_filter = ["category", "is_external_loanable"]
    search_fields = ["name", "short_code"]
