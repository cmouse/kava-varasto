from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm, AdminUserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


class ForcePasswordChangeMixin:
    """Force must_change_password=True whenever an admin sets a *usable*
    password (user creation or password reset)."""

    def set_password_and_save(self, user, commit=True, **kwargs):
        user = super().set_password_and_save(user, commit=False, **kwargs)
        if user.has_usable_password():
            user.must_change_password = True
        if commit:
            user.save()
        return user


class ForcedPasswordUserCreationForm(ForcePasswordChangeMixin, AdminUserCreationForm):
    pass


class ForcedPasswordChangeForm(ForcePasswordChangeMixin, AdminPasswordChangeForm):
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = ForcedPasswordUserCreationForm
    change_password_form = ForcedPasswordChangeForm
    fieldsets = DjangoUserAdmin.fieldsets + ((_("Password policy"), {"fields": ("must_change_password",)}),)
    list_filter = DjangoUserAdmin.list_filter + ("must_change_password",)
