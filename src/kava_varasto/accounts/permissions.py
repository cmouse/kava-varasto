from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated


class IsAuthenticatedAndPasswordCurrent(IsAuthenticated):
    """Authenticated, and not owing a forced password change.

    An admin-set password always arms must_change_password (see
    accounts/admin.py), so every account starts out with a password its
    issuer knows. The SPA hides the whole app behind ChangePasswordForm while
    the flag is set (frontend/src/components/Layout.jsx), but that is a
    rendering decision: without this check the session can still call every
    endpoint directly, and an account that never rotates its issued password
    keeps working access indefinitely.

    The endpoints needed to *clear* the flag -- change-password, me, logout --
    set their own permission_classes and are deliberately not covered.
    """

    message = _("Password change required.")

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return not request.user.must_change_password
