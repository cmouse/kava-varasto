from .base import *  # noqa: F403
from .base import REST_FRAMEWORK, env

DEBUG = False

SECRET_KEY = env("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# Trust the reverse proxy's forwarded headers (see README.md for the nginx recipe).
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# How many proxies append to X-Forwarded-For between the client and gunicorn.
# The login throttle buckets on the address this picks out of that chain, so
# getting it wrong either shares one bucket between every client (too low, if
# the proxy hides them) or lets a client mint a fresh bucket per request by
# prepending its own X-Forwarded-For (too high). One reverse proxy is the
# documented deployment; env-configurable so a CDN in front is a config change.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "NUM_PROXIES": env.int("DJANGO_NUM_PROXIES", default=1),
    # The SPA only ever consumes JSON. DRF's default renderer list also
    # carries BrowsableAPIRenderer, which serves an HTML API console (and an
    # HTML 403 naming the endpoint) to anyone who asks with Accept: text/html
    # -- surface with no consumer in production.
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Console-only: gunicorn's stdout/stderr is what gets captured (systemd/
# journald or similar) in this deploy model, no file rotation needed.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
