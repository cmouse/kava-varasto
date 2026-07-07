"""Local-only helper: mimics a reverse proxy's subpath strip (see the nginx
recipe in README.md) so sub-path mounting can be verified without installing
nginx. Django's runserver cannot route a subpath at all, so this wraps the
real WSGI app with a tiny shim that strips the configured prefix from
PATH_INFO before handing the request to Django -- exactly what nginx's
`proxy_pass` with trailing slashes does in production.

Usage:
    DJANGO_SETTINGS_MODULE=kava_varasto.settings.dev \
    DJANGO_FORCE_SCRIPT_NAME=/varasto DJANGO_SECRET_KEY=dev \
    gunicorn scripts.subpath_dev:application --bind 127.0.0.1:8010

Then browse http://127.0.0.1:8010/varasto/admin/
"""

import os

from kava_varasto.wsgi import application as django_app

PREFIX = os.environ.get("DJANGO_FORCE_SCRIPT_NAME", "/varasto")


def application(environ, start_response):
    path = environ.get("PATH_INFO", "")
    if path.startswith(PREFIX):
        environ["PATH_INFO"] = path[len(PREFIX):] or "/"
    # Intentionally does NOT set SCRIPT_NAME here -- mirrors nginx's
    # proxy_pass strip exactly, which also never sets SCRIPT_NAME.
    # FORCE_SCRIPT_NAME (settings, env-driven) supplies the prefix for
    # outgoing links instead.
    return django_app(environ, start_response)
