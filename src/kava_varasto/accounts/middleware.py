from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _

from .throttling import LoginRateThrottle


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
        # Test the path first: request.user is lazy, and touching it costs a
        # session read plus a user query on every SPA page load and every 404,
        # none of which this middleware has any opinion about.
        #
        # reverse() carries FORCE_SCRIPT_NAME and so does request.path, so
        # these compare correctly under sub-path mounting.
        if request.path.startswith(reverse("admin:index")) and not request.path.startswith(
            reverse("admin:logout")
        ):
            # Not getattr(): if this ever ends up above AuthenticationMiddleware
            # the gate should crash, not silently wave everyone through.
            user = request.user
            if user.is_authenticated and user.must_change_password:
                return redirect(reverse("spa") + "account/password")
        return self.get_response(request)


class AdminLoginThrottleMiddleware:
    """Rate-limit the Django admin's login form.

    LoginRateThrottle is wired into the API's LoginView by DRF itself, but the
    admin login is a second unthrottled credential endpoint on the same
    accounts. It is a plain Django view, so apply the same throttle -- and the
    same counter, since the two forms guess the same passwords -- here.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path == reverse("admin:login"):
            throttle = LoginRateThrottle()
            if not throttle.allow_request(request, None):
                response = HttpResponse(
                    _("Too many login attempts. Try again later."),
                    content_type="text/plain; charset=utf-8",
                    status=429,
                )
                wait = throttle.wait()
                if wait is not None:
                    response.headers["Retry-After"] = str(int(wait) + 1)
                return response
        return self.get_response(request)
