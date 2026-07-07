# TODO

Foundation/infrastructure is done. Remaining work, roughly in priority order:

## Domain models
- [ ] Equipment (name, optional short code e.g. X75/M96, quantity, category FK, member-only vs external-loanable flag)
- [ ] Category model + browsing
- [ ] Loan/Borrow (equipment FK, freeform borrower name, borrower->User mapping, borrow date, due date, checkout/checkin timestamps)

## Auth / accounts
- [ ] Document createsuperuser flow using accounts.User in README
- [ ] Borrower-name -> User mapping UX

## Borrowing workflow
- [ ] Checkout / check-in views
- [ ] Active vs historical loan listings

## Search & browsing
- [ ] Search by name/short code, category filter buttons

## UI/templates
- [x] Base template, mobile-first layout — SPA shell (`templates/spa.html`) + React/Bootstrap navbar in `frontend/src/components/Layout.jsx`
- [ ] Static asset serving strategy: whitenoise vs nginx-served (pick one)
- [x] Language switcher UI (backend plumbing for /i18n/setlang/ already in place, see README)
- [ ] Equipment/loan pages in the SPA (currently just a login screen + placeholder home page — see `frontend/src/pages/`)
- [ ] Cache-busting for frontend assets: `vite.config.js` currently emits fixed, unhashed `main.js`/`main.css` for simplicity; switch to hashed filenames + a manifest-reading template tag once repeat deploys need cache invalidation
- [ ] Add `npm ci && npm run build` (in `frontend/`) to the deploy steps in README, before `collectstatic`

## Localization
- [ ] Run `django-admin makemessages -l fi -l en` and translate real UI strings once templates exist
- [ ] `compilemessages` as part of the deploy step

## Production hardening
- [ ] SECURE_HSTS_SECONDS, SESSION/CSRF_COOKIE_SECURE, logging config
- [ ] Real SECRET_KEY generation/storage docs
- [ ] psycopg2-binary/mysqlclient only if/when Postgres/MySQL chosen
- [ ] pyproject.toml license field

## Sub-path mounting follow-ups (base mechanism already works)
- [ ] Consider dynamic SCRIPT_NAME via uwsgi native protocol (no-restart relocation) if the static env-var approach proves too rigid

## Testing / CI
- [ ] Real model + workflow tests once models exist
- [ ] CI running pytest + `manage.py check --deploy`
