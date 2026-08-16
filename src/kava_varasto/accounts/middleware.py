from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """Keep users who owe a password change out of the Django admin.

    IsAuthenticatedAndPasswordCurrent covers the REST API, but the admin is a
    second, equally complete way into the same data and knows nothing about
    must_change_password. Send those sessions to the SPA's change-password
    screen, which is the one place that clears the flag.

    Admin logout stays reachable so a redirected user is not stuck.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.must_change_password:
            # reverse() carries FORCE_SCRIPT_NAME, request.path carries the
            # same prefix, so these compare correctly under sub-path mounting.
            if request.path.startswith(reverse("admin:index")) and not request.path.startswith(
                reverse("admin:logout")
            ):
                return redirect(reverse("spa") + "account/password")
        return self.get_response(request)
