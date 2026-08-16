from django.conf import settings
from django.core.checks import Error

DUMMY_BACKEND = "django.core.cache.backends.dummy.DummyCache"


def check_login_throttle_cache(app_configs, **kwargs):
    """A no-op cache turns the login throttle off without saying so.

    LoginRateThrottle keeps its counters in CACHES["default"]; DRF reads them
    back, finds nothing, and allows every attempt -- no exception, no log line,
    and no test would catch it because the settings still name a throttle. Fail
    the deploy check instead. See DESIGN.md, "Login rate limiting".
    """
    if settings.CACHES.get("default", {}).get("BACKEND") != DUMMY_BACKEND:
        return []
    return [
        Error(
            "CACHES['default'] is DummyCache, which silently disables the login "
            "rate limit -- the only brute-force control on the admin and API "
            "login forms.",
            hint="Use a real cache backend; LocMemCache is what settings/base.py sets.",
            id="accounts.E001",
        )
    ]
