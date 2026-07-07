from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Loan, LoanItem


class LoanItemInline(admin.TabularInline):
    model = LoanItem
    extra = 1
    fields = ["equipment", "quantity", "quantity_returned"]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ["borrower_name", "borrower_phone", "due_date", "responsible", "is_returned", "returned_by"]
    list_filter = ["due_date"]
    search_fields = ["borrower_name", "borrower_phone"]
    readonly_fields = ["responsible", "returned_by", "returned_at", "created_at"]
    inlines = [LoanItemInline]

    @admin.display(boolean=True, description=_("returned"))
    def is_returned(self, obj):
        return obj.is_returned

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.responsible = request.user
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.mark_returned_if_complete(request.user)
