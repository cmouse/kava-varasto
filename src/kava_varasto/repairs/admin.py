from django import forms
from django.contrib import admin

from .models import RepairTicket


class RepairTicketAdminForm(forms.ModelForm):
    """Keeps the resolution fields in step with a status change.

    The stamping has to happen during form validation, not in
    ModelAdmin.save_model(): the form runs the model's full_clean() first, so
    a status change left unstamped is rejected as a validation error before
    save_model() ever gets a chance to fix it up. resolved_at/resolved_by are
    readonly, hence absent from the form, so construct_instance() leaves what
    set_status() put on the instance alone.
    """

    class Meta:
        model = RepairTicket
        fields = "__all__"

    # Bound to the logged-in user by RepairTicketAdmin.get_form(), which
    # builds a fresh subclass per request rather than mutating this one.
    user = None

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        if status is not None:
            self.instance.set_status(status, self.user)
        return cleaned_data


@admin.register(RepairTicket)
class RepairTicketAdmin(admin.ModelAdmin):
    form = RepairTicketAdminForm
    list_display = ["title", "status", "reported_by", "reported_at", "resolved_by", "resolved_at"]
    list_filter = ["status"]
    search_fields = ["title", "description"]
    filter_horizontal = ["equipment"]
    # reported_by and the resolution pair are stamped from the logged-in user;
    # editing them by hand would let them drift out of step with the status.
    readonly_fields = ["reported_by", "reported_at", "resolved_by", "resolved_at"]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # A per-request subclass, not an attribute set on `form` itself: the
        # admin reads base_fields off whatever this returns, so it has to stay
        # a form class, and a shared class would leak one request's user into
        # the next.
        return type(form.__name__, (form,), {"user": request.user})

    def save_model(self, request, obj, form, change):
        if not change:
            obj.reported_by = request.user
        super().save_model(request, obj, form, change)
