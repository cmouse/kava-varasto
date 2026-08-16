# kava-varasto

Storage bookkeeping system for Karhunvartijat ry: equipment stock and loans,
Django + React SPA, mountable under any URL prefix.

Design and rationale: `DESIGN.md`. Development, testing, releasing:
`DEVELOPMENT.md`.

## Requirements

- Python 3.11+
- Node.js 22+ (builds the frontend)
- gettext (`compilemessages`)
- SQLite (bundled with Python); no other services

## Install

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cd frontend && npm ci && npm run build && cd ..

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

App at `http://127.0.0.1:8000/`, admin at `http://127.0.0.1:8000/admin/`.

Further accounts are created in the admin (`/admin/accounts/user/add/`); an
admin-set password must be changed by its user at next login.

## Configuration

`kava_varasto.settings.dev` is used by `manage.py` and `pytest`;
`kava_varasto.settings.prod` by `wsgi.py`/`asgi.py`. Both read an optional
`.env` at the repo root. Copy `env.example` to `.env`.

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | insecure dev value (dev), required (prod) |
| `DJANGO_ALLOWED_HOSTS` | comma-separated allowed hosts | `*` (dev), required (prod) |
| `DJANGO_FORCE_SCRIPT_NAME` | sub-path this app is mounted under, e.g. `/varasto` (no trailing slash) | unset (domain root) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | comma-separated trusted origins, e.g. `https://webhost` | unset (prod only) |
| `DJANGO_NUM_PROXIES` | reverse proxies appending to `X-Forwarded-For`; picks the address the login throttle counts | `1` (prod only) |

Generate a key:

```sh
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

The database is not configurable: SQLite at `varasto.sqlite3` in the repo root.

## Install for production

Build and collect before starting gunicorn:

```sh
cd frontend && npm ci && npm run build && cd ..
DJANGO_SETTINGS_MODULE=kava_varasto.settings.prod python manage.py migrate
DJANGO_SETTINGS_MODULE=kava_varasto.settings.prod python manage.py collectstatic --noinput
DJANGO_SETTINGS_MODULE=kava_varasto.settings.prod python manage.py compilemessages
DJANGO_SETTINGS_MODULE=kava_varasto.settings.prod python manage.py check --deploy
DJANGO_SETTINGS_MODULE=kava_varasto.settings.prod gunicorn kava_varasto.wsgi:application --bind 127.0.0.1:8000
```

gunicorn serves no files, so the proxy serves `STATIC_ROOT` and `MEDIA_ROOT`.
Under nginx, mounted at `/varasto`:

```
location /varasto/static/ {
    alias /path/to/kava-varasto/staticfiles/;
}

# Uploaded equipment photos. Plain files only: no index, no scripting handler.
location /varasto/media/ {
    alias /path/to/kava-varasto/media/;
}

location /varasto/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

- The trailing slashes on both `location` and `proxy_pass` strip `/varasto`
  before forwarding; `DJANGO_FORCE_SCRIPT_NAME=/varasto` adds it back to
  generated links, static/media URLs and cookie paths.
- `X-Forwarded-For` is required: the login throttle buckets on its last entry,
  and nginx forwards the client's own header unless this directive appends the
  real address. Apache's `mod_proxy` appends by default.

Host prerequisites for the automated deploy (see `DEVELOPMENT.md`): SSH key in
`~/.ssh/authorized_keys`, `loginctl enable-linger <user>`, and a
`varasto@.service` templated user unit carrying the environment above.
