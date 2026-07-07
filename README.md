# kava-varasto

Storage bookkeeping system for Karhunvartijat ry — replaces a spreadsheet-based
stock/loan tracker. See `DESIGN.md` for the full requirements and `TODO.md`
for what's left to build.

## Requirements

- Python 3.11+
- Node.js 20+ (only needed to build the frontend)
- No external services required for local dev (SQLite by default)

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python manage.py migrate
python manage.py createsuperuser

cd frontend
npm install
npm run build
cd ..

python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the app, or `http://127.0.0.1:8000/admin/` for
the Django admin.

## Architecture

This is a single-page app: Django serves one HTML shell (`templates/spa.html`)
for every non-API route, and the React app in `frontend/` does all rendering
and interaction client-side, talking to the backend exclusively over the REST
API mounted under `/api/` (built with Django REST Framework, session-cookie
authenticated — see `kava_varasto.accounts.urls`).

`frontend/` is a separate Vite/React project:

- `npm run build` compiles it to `src/kava_varasto/static/frontend/`, which
  Django's staticfiles app picks up via `STATICFILES_DIRS`
  (`src/kava_varasto/settings/base.py`) — same `collectstatic`/nginx pipeline
  as any other static asset, see "Sub-path mounting" below.
- `npm run dev` runs the Vite dev server with hot reload; it proxies `/api/`
  and `/i18n/` to a Django dev server running on `127.0.0.1:8000` (see
  `frontend/vite.config.js`), so run both `manage.py runserver` and
  `npm run dev` side by side and browse the Vite dev server's own port
  instead of Django's.

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
location /varasto/static/ {
    alias /path/to/kava-varasto/staticfiles/;
}

location /varasto/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
}
```

gunicorn never serves static files itself (that's true regardless of
sub-path mounting), so nginx must serve `STATIC_ROOT` directly — build the
frontend and collect static files under prod settings before starting
gunicorn:

```sh
cd frontend
npm ci
npm run build
cd ..
DJANGO_SETTINGS_MODULE=kava_varasto.settings.prod python manage.py collectstatic --noinput
```

The trailing slashes on
both the app `location` and `proxy_pass` make nginx strip `/varasto` before
forwarding — gunicorn/Django think they're serving from `/`. Setting
`DJANGO_FORCE_SCRIPT_NAME=/varasto` (e.g. in the gunicorn service's
environment) adds the prefix back for generated links and static
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
`Accept-Language` header, falling back to `LANGUAGE_CODE`). The navbar's
language switcher (`frontend/src/components/LanguageSwitcher.jsx`) posts to
`/i18n/setlang/` to switch language explicitly (see `django.conf.urls.i18n`).

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
