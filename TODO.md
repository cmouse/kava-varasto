# TODO

Foundation/infrastructure is done. Remaining work, roughly in priority order:

## Domain models
- [x] Equipment (name, optional short code e.g. X75/M96, quantity, category FK, member-only vs external-loanable flag) — `kava_varasto.inventory.models.Equipment`, registered in admin
- [x] Category model — `kava_varasto.inventory.models.Category`, registered in admin
- [ ] Category browsing UI (search/filter buttons in the SPA)
- [x] Loan/Borrow model (borrower name+phone, due date, details, per-item quantity/quantity_returned for partial returns, responsible/returned_by tied to logged-in users, no delete) — `kava_varasto.loans.models.Loan`/`LoanItem`, registered in admin

## Auth / accounts
- [ ] Document createsuperuser flow using accounts.User in README
- [ ] Borrower-name -> User mapping UX

## Borrowing workflow
- [x] Checkout (loan creation) view, with stock-out limit enforcement — `kava_varasto.loans.views.LoanCreateView`, `frontend/src/pages/LoanNew.jsx`
- [ ] Check-in view
- [ ] Active vs historical loan listings

## Search & browsing
- [ ] Search by name/short code, category filter buttons

## UI/templates
- [x] Base template, mobile-first layout — SPA shell (`templates/spa.html`) + React/Bootstrap navbar in `frontend/src/components/Layout.jsx`
- [ ] Static asset serving strategy: whitenoise vs nginx-served (pick one)
- [x] Language switcher UI (backend plumbing for /i18n/setlang/ already in place, see README)
- [x] Equipment storage view in the SPA (read-only stock levels: quantity/broken/available) — `frontend/src/pages/Storage.jsx`, `GET /api/inventory/equipment/`
- [x] Loan creation page in the SPA (add/remove items, stock-out limit enforcement) — `frontend/src/pages/LoanNew.jsx`, `POST /api/loans/`
- [ ] Loan check-in/return UI, active vs historical listings in the SPA
- [x] Cache-busting for frontend assets: `vite.config.js` emits hashed filenames + a manifest; `spa.html` resolves them via the `vite_asset`/`vite_css` template tags (`src/kava_varasto/templatetags/vite.py`)
- [x] Add `npm ci && npm run build` (in `frontend/`) to the deploy steps in README, before `collectstatic`
- [ ] Business logo in the header — download https://www.karhunvartijat.net/site/wp-content/uploads/2020/03/cropped-cropped-cropped-b84547adb1de4692e50ae00ea9a882beJH1exUFYMMKpHQn4-0-1-e1711610706918.png into the repo (frontend asset), don't hotlink it

## Localization
- [x] Wire an i18n library into the React frontend (react-i18next) with FI/EN string
      catalogs for existing components (`frontend/src/i18n/`) — language is read from
      the server-rendered `<html lang>` (which the existing `/i18n/setlang/` flow
      controls), confirmed by manual test that switching FI/EN in the navbar flips all
      SPA component strings
- [ ] Add new component strings to `frontend/src/i18n/locales/{en,fi}.json` as the SPA grows
      (equipment/loan pages etc.)
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

## Repository / GitHub publishing (future)
- [ ] Create SECURITY.md
- [ ] Create LICENSE.md
- [ ] Add .github/workflows for when this is pushed to GitHub — we publish packages only (no container images/deploy targets)
