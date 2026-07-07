# TODO

Foundation/infrastructure is done. Remaining work, roughly in priority order:

## Domain models
- [x] Equipment (name, optional short code e.g. X75/M96, quantity, category FK, member-only vs external-loanable flag) — `kava_varasto.inventory.models.Equipment`, registered in admin
- [x] Category model — `kava_varasto.inventory.models.Category`, registered in admin
- [x] Category browsing UI (search/filter buttons in the SPA) — `frontend/src/hooks/useEquipmentFilter.js`, `frontend/src/components/EquipmentFilterBar.jsx`
- [x] Loan/Borrow model (borrower name+phone, due date, details, per-item quantity/quantity_returned for partial returns, responsible/returned_by tied to logged-in users, no delete) — `kava_varasto.loans.models.Loan`/`LoanItem`, registered in admin

## Auth / accounts
- [x] Document createsuperuser flow using accounts.User in README — see "Creating additional user accounts" in README.md
- [x] Borrower-name autofill from loan history — `<datalist>` in `frontend/src/pages/LoanNew.jsx`, no real `User` account link (see DESIGN.md)
- [x] Password change form so users can change their own password — `POST /api/accounts/change-password/`, `frontend/src/pages/ChangePassword.jsx`
- [x] Require password change on first use — `must_change_password` on `accounts.User`, forced via `accounts/admin.py`, gated in `frontend/src/components/Layout.jsx`

## Borrowing workflow
- [x] Checkout (loan creation) view, with stock-out limit enforcement — `kava_varasto.loans.views.LoanListCreateView`, `frontend/src/pages/LoanNew.jsx`
- [x] Loan form input validation: phone number in `+358xxx` or `0xxx` format, borrower name must have at least two parts, due date defaults to +1 week and can't be in the past — `LoanCreateSerializer` in `kava_varasto.loans.serializers`, mirrored client-side in `frontend/src/pages/LoanNew.jsx`
- [x] Check-in view — `POST /api/loans/<id>/return/` (`kava_varasto.loans.views.LoanReturnView`), `frontend/src/pages/LoanReturn.jsx`, supports partial returns
- [x] Active vs historical loan listings — `GET /api/loans/`, `frontend/src/pages/LoanList.jsx`

## Search & browsing
- [x] Search by name/short code, category filter buttons — client-side filtering in `Storage.jsx` and `LoanNew.jsx` via `useEquipmentFilter`

## UI/templates
- [x] Base template, mobile-first layout — SPA shell (`templates/spa.html`) + React/Bootstrap navbar in `frontend/src/components/Layout.jsx`
- [x] Static asset serving strategy: nginx-served — see README's "Production (gunicorn behind nginx)" section
- [x] Language switcher UI (backend plumbing for /i18n/setlang/ already in place, see README)
- [x] Equipment storage view in the SPA (read-only stock levels: quantity/broken/available, real-time availability accounting for active loans) — `frontend/src/pages/Storage.jsx`, `GET /api/loans/loanable-equipment/`
- [x] Loan creation page in the SPA (add/remove items, stock-out limit enforcement) — `frontend/src/pages/LoanNew.jsx`, `POST /api/loans/`
- [x] Loan overview page in the SPA (active vs historical listings) — `frontend/src/pages/LoanList.jsx`, `GET /api/loans/`
- [x] Loan check-in/return UI in the SPA — `frontend/src/pages/LoanReturn.jsx`, `POST /api/loans/<id>/return/`
- [x] Cache-busting for frontend assets: `vite.config.js` emits hashed filenames + a manifest; `spa.html` resolves them via the `vite_asset`/`vite_css` template tags (`src/kava_varasto/templatetags/vite.py`)
- [x] Add `npm ci && npm run build` (in `frontend/`) to the deploy steps in README, before `collectstatic`
- [x] Business logo in the header — `frontend/src/assets/logo.png`, shown in `frontend/src/components/Layout.jsx`'s navbar brand

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
- [x] SECURE_HSTS_SECONDS, SESSION/CSRF_COOKIE_SECURE, logging config — `kava_varasto.settings.prod`, confirmed via `manage.py check --deploy`
- [x] Real SECRET_KEY generation/storage docs — see README's "Generating a SECRET_KEY" section
- [ ] psycopg2-binary/mysqlclient only if/when Postgres/MySQL chosen
- [ ] pyproject.toml license field

## Sub-path mounting follow-ups (base mechanism already works)
- [ ] Consider dynamic SCRIPT_NAME via uwsgi native protocol (no-restart relocation) if the static env-var approach proves too rigid

## Testing / CI
- [ ] Real model + workflow tests once models exist
- [x] CI running pytest + `manage.py check --deploy` — `.github/workflows/ci.yml`

## Repository / GitHub publishing (future)
- [ ] Create SECURITY.md
- [ ] Create LICENSE.md
- [ ] Add .github/workflows for when this is pushed to GitHub — we publish packages only (no container images/deploy targets)
