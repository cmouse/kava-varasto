# kava-varasto

Storage bookkeeping system for Karhunvartijat ry — replaces a spreadsheet-based
stock/loan tracker. See `DESIGN.md` for the full requirements and `TODO.md`
for what's left to build.

## Requirements

- Python 3.11+
- No external services required for local dev (SQLite by default)

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/` and log in.

## Configuration

Settings are split into `kava_varasto.settings.dev` (used by `manage.py` and
`pytest` by default) and `kava_varasto.settings.prod` (used by `wsgi.py`/
`asgi.py` by default — fails loudly if misconfigured, no insecure fallbacks).
Both read from an optional `.env` file at the repo root via `django-environ`.
Copy `env.example` to `.env` and adjust as needed. Relevant variables:

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | `django-environ` DB URL, e.g. `postgres://user:pass@host:5432/db` | `sqlite:///db.sqlite3` |
| `DJANGO_SECRET_KEY` | Django secret key | insecure dev-only value (dev), required (prod) |
| `DJANGO_ALLOWED_HOSTS` | comma-separated allowed hosts | `*` (dev), required (prod) |
| `DJANGO_FORCE_SCRIPT_NAME` | sub-path this app is mounted under, e.g. `/varasto` (no trailing slash) | unset (serve from domain root) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | comma-separated trusted origins, e.g. `https://webhost` | unset (prod only) |

## Testing

```sh
pytest
```

## Sub-path mounting

This app is designed to be relocatable — installable as a package and
deployable under any URL prefix, not just the domain root. `DJANGO_FORCE_SCRIPT_NAME`
drives `FORCE_SCRIPT_NAME`, `STATIC_URL`, `MEDIA_URL`, and cookie paths
together (see `src/kava_varasto/settings/base.py`), so they can't drift out
of sync.

### Production (gunicorn behind nginx)

```
location /varasto/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
}
```

The trailing slashes on both `location` and `proxy_pass` make nginx strip
`/varasto` before forwarding — gunicorn/Django think they're serving from
`/`. Setting `DJANGO_FORCE_SCRIPT_NAME=/varasto` (e.g. in the gunicorn
service's environment) adds the prefix back for generated links and static
URLs. Run gunicorn with production settings:

```sh
DJANGO_SETTINGS_MODULE=kava_varasto.settings.prod gunicorn kava_varasto.wsgi:application --bind 127.0.0.1:8000
```

### Local verification without nginx

`manage.py runserver` cannot route a subpath at all, so use the included
helper, which reproduces nginx's exact strip-then-readd split:

```sh
DJANGO_SETTINGS_MODULE=kava_varasto.settings.dev \
DJANGO_FORCE_SCRIPT_NAME=/varasto DJANGO_SECRET_KEY=dev \
gunicorn scripts.subpath_dev:application --bind 127.0.0.1:8010
```

Then browse `http://127.0.0.1:8010/varasto/admin/` and confirm the login
form and static CSS both carry the `/varasto/` prefix.

## Localization

The site defaults to Finnish (`fi`) with English (`en`) available. Language
is picked via the standard Django flow (session, cookie, then the
`Accept-Language` header, falling back to `LANGUAGE_CODE`). `POST` to
`/i18n/setlang/` to switch language explicitly (see
`django.conf.urls.i18n` — a UI for this is still on `TODO.md`).

Once real UI strings exist beyond Django's own bundled translations:

```sh
django-admin makemessages -l fi -l en
# translate the generated .po files under locale/
django-admin compilemessages
```

## Deployment notes

No Docker setup — deploy as a plain WSGI app (gunicorn) behind a reverse
proxy such as nginx. See `TODO.md` for outstanding production-hardening
items (HSTS, secure cookies, logging, etc.) before going live.
