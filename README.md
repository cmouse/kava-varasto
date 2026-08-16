# kava-varasto

Storage bookkeeping system for Karhunvartijat ry — replaces a spreadsheet-based
stock/loan tracker. See `DESIGN.md` for the full requirements and `TODO.md`
for what's left to build.

## Requirements

- Python 3.11+
- Node.js 22+ (only needed to build the frontend)
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

### Creating additional user accounts

There's no signup or account-creation API — regular staff accounts are
created through the Django admin (`/admin/accounts/user/add/`) by an
existing superuser. Whenever an admin creates a new account, or resets an
existing user's password via the admin's "change password" screen, that
account is automatically flagged to require a password change: the user
must set a new password immediately after their next login, before they
can use the rest of the app. This does **not** apply to the initial
superuser created via `createsuperuser` above, nor to any password a user
sets for themselves — users can change their own password anytime from the
navbar ("Change password").

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

The database is not configurable: SQLite at `varasto.sqlite3` in the repo
root (WAL journal mode, `busy_timeout=5000`, immediate transactions).

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | insecure dev-only value (dev), required (prod) |
| `DJANGO_ALLOWED_HOSTS` | comma-separated allowed hosts | `*` (dev), required (prod) |
| `DJANGO_FORCE_SCRIPT_NAME` | sub-path this app is mounted under, e.g. `/varasto` (no trailing slash) | unset (serve from domain root) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | comma-separated trusted origins, e.g. `https://webhost` | unset (prod only) |
| `DJANGO_NUM_PROXIES` | reverse proxies in front of gunicorn; picks the client address the login throttle counts | `1` (prod only) |

### Generating a SECRET_KEY

```sh
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Store the result in `DJANGO_SECRET_KEY` via an environment variable or your
deployment's secrets manager — never commit it (`.env` is already
gitignored).

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
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

`X-Forwarded-For` is not optional: the login throttle buckets on the last
entry of that header (`DJANGO_NUM_PROXIES`), and nginx forwards whatever
the client sent unless this directive appends the real address. Without it
a client picks its own throttle bucket. Apache's `mod_proxy` appends on its
own, so an Apache front end needs nothing extra here.

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
DJANGO_SETTINGS_MODULE=kava_varasto.settings.prod python manage.py compilemessages
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

## Releasing

Versioning lives in one place: the `version` field in `pyproject.toml`
(`frontend/package.json`'s version is unused, the frontend ships bundled
inside the backend package). To cut a release:

1. Bump `version` in `pyproject.toml` (e.g. `0.2.0`), commit.
2. Tag it to match, prefixed with `v`: `git tag v0.2.0`.
3. `git push --tags`.

Pushing a matching `vX.Y.Z` tag runs `.github/workflows/publish.yml`, which
lints and tests the backend and frontend, then — only if the tag matches
`pyproject.toml`'s version — builds a Python sdist/wheel and attaches them
to a new GitHub Release. No PyPI/npm publish and no container images: this
project publishes downloadable release artifacts only, not to a registry.

## Deployment notes

No Docker setup — deploy as a plain WSGI app (gunicorn) behind a reverse
proxy such as nginx. `kava_varasto.settings.prod` (used by `wsgi.py`/
`asgi.py`) already enables HSTS, forces secure session/CSRF cookies, and
logs to the console (captured by systemd/journald or your process
supervisor) — nothing further to configure for these. Run
`manage.py check --deploy` under prod settings before going live to confirm.

### Automated deployment

`.github/workflows/deploy.yml` deploys automatically once the `CI` workflow
has finished **successfully** for the same commit — a red build never
reaches a host, and the checks are not re-run by the deploy itself:

| Trigger | Target |
| --- | --- |
| push to `main` | `staging` environment |
| push of a `vX.Y.Z` tag | `production` environment |

Which target a run belongs to is decided by the `target` job, which asks git
which `v*.*.*` tag points at the commit rather than trusting the branch name
GitHub reports for a tag push. A tag that does not match `pyproject.toml`'s
version fails the run outright — the same rule `publish.yml` enforces.

Each GitHub environment supplies the target's address, location and
credentials:

- `HOST`, `USER` and `INSTALL_PATH` — environment *variables*.
  `INSTALL_PATH` is the deploy directory, either absolute or relative to
  `USER`'s home (`varasto`, not `~/varasto` — a leading `~` is rejected,
  because only some of the steps run it through a shell that would expand
  it). It has no default, and an empty value fails the run rather than
  writing to the home root.
- `SSH_KEY` — environment *secret*, a private key authorised for `USER` on
  `HOST`

Both targets share the steps in `.github/actions/deploy`, and a deploy is
deliberately just two things: rsync the tree to `INSTALL_PATH`, then
`systemctl --user restart varasto@<environment>` (`varasto@staging` or
`varasto@production`). The unit runs `start.sh`, which builds
the frontend, migrates, collects static files and compiles translations
before exec'ing gunicorn — so the restart *is* the deploy, and CI never
needs the app's production environment. The one extra step is a copy of
`varasto.sqlite3` taken before the restart, since `start.sh` migrates on
every start and migrations do not roll back.

The app is deployed as a checkout rather than as an installed wheel, because
`BASE_DIR` is derived from the repo root — `templates/`, `locale/`,
`staticfiles/`, `media/` and `varasto.sqlite3` must sit next to `src/`. The
rsync deliberately runs without `--delete` and excludes `.env`,
`varasto.sqlite3*`, `media/`, `staticfiles/` and `.venv/`, so host-local
state is never touched.

Set up on the host before the first deploy — none of this can be done from
CI:

1. `USER`'s public key in `~/.ssh/authorized_keys`.
2. `loginctl enable-linger <user>`, so the user's systemd instance and
   `/run/user/<uid>` exist without an active login session. Without it the
   `systemctl --user restart` step fails.
3. A `varasto@.service` templated user unit running `start.sh`, enabled for
   the instance named after the environment (`varasto@staging`,
   `varasto@production`), carrying `DJANGO_SECRET_KEY`,
   `DJANGO_ALLOWED_HOSTS` and the rest of the app's environment — the deploy
   supplies none of it, and `.env` is never rsynced.
4. Whatever `start.sh` itself needs: `python3` with the project installed,
   Node for `npm ci && npm run build`, and `gettext` for
   `compilemessages`.
