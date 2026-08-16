# Development

Install: see `README.md`. Design and rationale: `DESIGN.md`.

## Frontend

`frontend/` is a separate Vite/React project.

```sh
cd frontend
npm run build   # compiles to src/kava_varasto/static/frontend/, picked up by STATICFILES_DIRS
npm run dev     # Vite dev server with hot reload, proxies /api/ and /i18n/ to 127.0.0.1:8000
npm run lint
```

With `npm run dev`, run `manage.py runserver` alongside it and browse the Vite
port, not Django's.

## Tests

```sh
pytest
ruff check .
```

## Sub-path mounting

`manage.py runserver` cannot route a sub-path. `scripts/subpath_dev.py`
reproduces the proxy's strip-then-readd split:

```sh
DJANGO_SETTINGS_MODULE=kava_varasto.settings.dev \
DJANGO_FORCE_SCRIPT_NAME=/varasto DJANGO_SECRET_KEY=dev \
gunicorn scripts.subpath_dev:application --bind 127.0.0.1:8010
```

Browse `http://127.0.0.1:8010/varasto/admin/`; the login form and its CSS must
both carry the `/varasto/` prefix.

## Translations

Finnish by default, English available. The language is chosen by Django's
standard flow (session, cookie, `Accept-Language`, `LANGUAGE_CODE`); the navbar
switcher posts to `/i18n/setlang/`.

```sh
django-admin makemessages -l fi -l en
# translate locale/*/LC_MESSAGES/django.po
django-admin compilemessages
```

`.mo` files are gitignored and built on deploy. SPA strings live in
`frontend/src/i18n/`, not in the `.po` catalogs.

## Releasing

Version lives only in `pyproject.toml` (`frontend/package.json`'s version is
unused).

1. Bump `version`, commit.
2. `git tag vX.Y.Z` matching that version.
3. `git push --tags`.

A matching tag runs `.github/workflows/publish.yml`, which lints, tests, and
attaches an sdist and wheel to a GitHub Release. A tag that disagrees with
`pyproject.toml` fails the run. Nothing is published to PyPI or npm, and no
images are built.

## Automated deployment

`.github/workflows/deploy.yml` runs only after `CI` succeeds for the same
commit.

| Trigger | Target |
| --- | --- |
| push to `main` | `staging` environment |
| push of a `vX.Y.Z` tag | `production` environment |

Each GitHub environment supplies `HOST`, `USER` and `INSTALL_PATH` as variables
and `SSH_KEY` as a secret. `INSTALL_PATH` is absolute or relative to `USER`'s
home (`varasto`, not `~/varasto` — a leading `~` is rejected); an empty value
fails the run.

A deploy is an rsync to `INSTALL_PATH` plus `systemctl --user restart
varasto@<environment>`. The unit runs `start.sh`, which builds the frontend,
migrates, collects static files and compiles translations before exec'ing
gunicorn — so the restart is the deploy. The action takes a `varasto.sqlite3`
backup first, because migrations do not roll back.

The rsync runs without `--delete` and excludes `.env`, `varasto.sqlite3*`,
`media/`, `staticfiles/` and `.venv/`, so host-local state is never touched.
The app is deployed as a checkout, not a wheel: `BASE_DIR` is the repo root, so
`templates/`, `locale/`, `staticfiles/`, `media/` and `varasto.sqlite3` must sit
next to `src/`.

Rationale for these choices is in `DESIGN.md`, "Deployment automation".
