Storage bookkeeping system for Karhunvartijat ry
================================================

This system is intended to replace sheets based stock management and loaning system for non-profit.

Key requirements for this system:

 - Allow maintaining information about what equipment, and how much should be in storage.
 - Allow mapping equiment with short codes, or by name. (Some equipment has no short code)
 - Simple user management and authentication, only few users for the system. 
 - Needs to work sub-path mounting
 - Must have working mobile and pc UI, especially for borrowing equipment.
 - Must be localizable to Finnish and English, defaulting to Finnish.

Borrowing equipment
-------------------

The process for borrowing the equipment works by marking who is borrowing equipment, which is freeform,
and needs to be mapped to the current user. There should also be information when equipment was borrowed
and when it is suposed to be returned.

There should be way to search equipment by name and short code. Or using category buttons.

Then the borrowed equipment is checked out, and when user returns them, they are checked in.

There are some equipment that is borrowed for members of non-profit only, and small amount of equipment that is borrowed outside.

Short codes
-----------

Most equipment has short codes likes X75, or M96. But some equipment does not.

A short code identifies one specific physical item, so equipment with a short
code always has quantity 1. Equipment with no short code (e.g. "Trangia
stove") is tracked as a stock count instead -- quantity can be more than one,
so we know how many are in storage vs. borrowed. Enforced by
`Equipment.clean()` and a DB check constraint
(`kava_varasto.inventory.models.Equipment`).

Broken equipment
----------------

Equipment can be marked broken via `broken_quantity` (0 by default). For
short-coded items (quantity always 1) this is effectively a broken/not-broken
flag; for bulk stock (e.g. Trangia stoves) it tracks how many of the total are
currently broken, so `available_quantity` (quantity minus broken_quantity)
reflects what can actually be loaned out. Cannot exceed `quantity`, enforced
by `Equipment.clean()` and a DB check constraint.

Categorization
--------------
To make it easier to find equipment, there should be categories of equipment when borrowing, so that equipment with no short code is discoverable.

Listings
--------
All borrows need to be listable as active and old.

Loans
-----

A loan (`kava_varasto.loans.models.Loan`) records one borrower taking out
equipment: freeform `borrower_name` and `borrower_phone` (so the borrower can
be reached, no User mapping yet), a `due_date`, and a freeform `details`
field. Each piece of equipment on the loan is a `LoanItem` (equipment FK +
quantity), so a loan can cover several pieces of equipment at once.

`responsible` is the staff member who handed out the loan -- always the
logged-in user, set automatically (admin's `save_model`, not user-editable).

Equipment can be returned in parts: each `LoanItem.quantity_returned` tracks
how much of that item has come back, and can't exceed `quantity` (enforced by
`LoanItem.clean()` and a DB check constraint). Once every item on a loan is
fully returned, the loan is archived: `returned_at` and `returned_by` (the
staff member who processed the return) are set via
`Loan.mark_returned_if_complete()`, called from the admin after items are
saved.

Loans can never be deleted, only returned/archived --
`Loan.delete()` raises `PermissionDenied`, and the admin has delete
permission turned off.

Loan creation UI and stock-out limits
--------------------------------------

Staff create loans via the SPA (`frontend/src/pages/LoanNew.jsx`, `POST
/api/loans/`), picking any number of equipment rows to add/remove on one
form. Creating a loan sets `responsible` to the logged-in user automatically
(same rule as the admin), and rejects (400) if any requested quantity
exceeds what's actually free right now.

"Currently out" for a piece of equipment is computed on the fly as the sum
of `quantity - quantity_returned` across all its `LoanItem` rows (no need to
special-case archived loans -- a fully returned item already sums to 0).
`loanable_quantity = available_quantity - currently_out` is what
`LoanCreateSerializer.validate_items()` enforces, and what
`GET /api/loans/loanable-equipment/` (`kava_varasto.loans.views
.LoanableEquipmentListView`) reports, alongside the full equipment stock
fields (`quantity`, `broken_quantity`, `available_quantity`,
`is_external_loanable`). This lives in the `loans` app, not `inventory`,
since it's loan data -- `inventory` still has no reverse dependency on
`loans`.

This is a check-then-act validation with no row locking -- two staff
creating loans for the same last-remaining item at the same instant could
both pass validation. Accepted for this app's scale (few users, a single
non-profit's gear closet).

The read-only Storage view (`Storage.jsx`) now sources from
`GET /api/loans/loanable-equipment/` instead of the plain
`GET /api/inventory/equipment/`, so it shows real-time availability
(accounting for other active loans, not just broken stock) with a
badge for whether each item is currently available to loan. This
supersedes the earlier "no out column" scope decision. The
`inventory` equipment endpoint itself is unchanged and still exists
(own test coverage), just no longer the SPA's source for stock
display.

Loan overview page
-------------------

Staff view all loans via the SPA (`frontend/src/pages/LoanList.jsx`,
`GET /api/loans/` -- the same URL as loan creation, `POST`; DRF's
`ListCreateAPIView` dispatches by method), split into active (not yet
fully returned) and returned/historical sections client-side using the
`is_returned` field on `LoanSerializer`.

Loan check-in / return
-----------------------

Each active loan on `LoanList.jsx` has a "Return" button
(`frontend/src/pages/LoanReturn.jsx`, `/loans/:id/return`) that posts to
`POST /api/loans/<id>/return/` (`kava_varasto.loans.views.LoanReturnView`).
The page looks the loan up from the already-fetched `useLoans()` list
(no separate loan-detail endpoint) and shows one row per `LoanItem`: a
number input (defaulting to full quantity) for items not yet fully
returned, or a "fully returned" badge for items that are.

The request body is `{"items": [{"item": <LoanItem id>, "quantity_returned":
<int>}, ...]}` -- an absolute new total per item, same semantics as the
Django admin's inline field, not a delta. `LoanReturnSerializer`
(`loans/serializers.py`) rejects: items not belonging to the target loan,
a `quantity_returned` that decreases (returns are monotonic, no "undo"),
or one that exceeds `quantity`. The view rejects the whole request with
400 if the loan is already `is_returned`. Partial returns are allowed --
some items can be completed while others stay outstanding; the loan only
archives (`returned_at`/`returned_by` set) once every item is fully
returned, via the existing `Loan.mark_returned_if_complete()`, called
with the submitting user (same rule as loan creation's `responsible`).

Implementation note: `LoanReturnView` fetches the `Loan` *without*
`prefetch_related("items")`. Prefetching before mutating and saving the
`LoanItem` rows would leave the reverse-FK cache holding stale (pre-update)
instances, so both `mark_returned_if_complete()`'s own item check and the
response `LoanSerializer` would report outdated `quantity_returned` values
even though the DB was already correct. Leaving the queryset unprefetched
means every `.items.all()` access re-queries fresh.

Loan form input validation
---------------------------

`LoanCreateSerializer` (`loans/serializers.py`) validates three fields on
creation, in addition to the existing item/quantity checks:

- `borrower_name` must have at least two whitespace-separated parts (first
  and last name).
- `borrower_phone` must match `^(\+358\d{6,12}|0\d{6,12})$` -- a Finnish
  number starting with `+358` or a local `0` prefix.
- `due_date` must not be before today, using `timezone.localdate()` (not
  `.now().date()`) since the app runs with `TIME_ZONE = "Europe/Helsinki"`
  and `USE_TZ = True` -- comparing against the UTC date would reject valid
  dates or accept a past one near local midnight.

This is enforced only in the serializer (the SPA's one creation path), not
as a model-level `clean()`/DB constraint -- admin-created loans are trusted
staff input and out of scope. `LoanNew.jsx` mirrors the same rules
client-side via native HTML5 `pattern`/`min` attributes (no new per-field
error UI -- the app has none anywhere), and defaults the due-date field to
today+7 days.

Search / category browsing
----------------------------

`Storage.jsx` and `LoanNew.jsx`'s equipment picker both filter client-side
via the shared `frontend/src/hooks/useEquipmentFilter.js` hook -- no
django-filter or query-param plumbing was added, since `useLoanableEquipment()`
already fetches the full equipment list and the app's stated scale (few
users, one gear closet) doesn't warrant server-side search. The hook matches
`name`/`short_code` (case-insensitive substring) and an optional
`category_id`.

`LoanableEquipmentSerializer` (`loans/serializers.py`) gained an additive
`category_id` field (`PrimaryKeyRelatedField(source="category",
read_only=True)`) alongside the existing `category` name string, so category
filter buttons can key off a stable id instead of matching by name. The
plain `inventory` app endpoint/serializer is untouched -- the SPA has never
used it, only the loans app's annotated `loanable-equipment` endpoint.

`Storage.jsx` gets a full search box + category pill buttons
(`EquipmentFilterBar.jsx`). `LoanNew.jsx`'s picker gets a search box only
(its rows aren't a table, so pill buttons don't fit) plus `<optgroup>`
grouping by category inside each row's `<select>`; if a row's already-chosen
equipment gets excluded by a new search term, its option is spliced back in
from the unfiltered list so the dropdown never silently loses the visible
selection.

Password policy
-----------------

`accounts.User` has a `must_change_password` boolean (default `False`),
exposed on `UserSerializer` so `/me/` and `/login/` responses carry it.
`POST /api/accounts/change-password/` (`ChangePasswordSerializer` +
`ChangePasswordView`) lets a logged-in user set their own password:
`current_password` must check out via `check_password`, `new_password`
runs through Django's `AUTH_PASSWORD_VALIDATORS`, and a successful change
clears the flag and calls `update_session_auth_hash()` so the session
survives.

The flag is forced to `True` whenever *staff* set a password through the
Django admin -- both "add user" and "reset password" funnel through
`SetPasswordMixin.set_password_and_save()` (Django 5.2), so
`ForcePasswordChangeMixin` in `accounts/admin.py` overrides that one method,
delegates with `commit=False`, and only forces the flag if
`user.has_usable_password()` (so an admin explicitly leaving a user
passwordless -- SSO-only -- isn't wrongly flagged). `createsuperuser` never
touches these admin forms, so the bootstrap superuser is never gated.

`Layout.jsx` centralizes the frontend gate: when the logged-in user's
`must_change_password` is true, it renders `<ChangePasswordForm forced />`
in place of `<Outlet/>` (navbar/logout stay usable) rather than repeating
the per-page auth-guard pattern used elsewhere. This is a frontend-only
gate -- the API itself doesn't block other endpoints for a flagged user,
an accepted tradeoff at this app's few-trusted-staff scale.

Borrower name/phone autofill
-----------------------------

`LoanNew.jsx` reuses the already-fetched, unpaginated `GET /api/loans/`
(`useLoans()`, no backend changes) to remember past borrowers: a
`<datalist>` on the borrower name field offers every distinct
`borrower_name` seen before, and picking (or exactly retyping) one
autofills `borrower_phone` from that borrower's most recent loan -- only
when the phone field is still empty, so a manual edit is never clobbered.

This is convenience autofill, not an account link -- it matches purely on
the freeform name string and has no relation to `accounts.User`. This isn't
a scope tradeoff: only staff -- the people handing equipment out and
processing returns (`responsible`/`returned_by`) -- ever have `User`
accounts. Borrowers never do, so a `Loan.borrower_user` FK to `User` isn't
a smaller version of the right feature, it's modeling a relationship that
doesn't exist in this domain. No new endpoint or migration was needed since
`LoanList.jsx`/`LoanReturn.jsx` already rely on the same unpaginated loan
list.

Django-side translations
--------------------------

`LOCALE_PATHS = [BASE_DIR / "locale"]` was already set, but `locale/` had
never been generated. `django-admin makemessages -l fi -l en` now extracts
the ~35 real `gettext_lazy`/`_()` call sites that already existed in the
code -- model `verbose_name`/`help_text` (inventory/loans/accounts models),
admin fieldset/list_display labels, and DRF `ValidationError` messages in
the loans/accounts serializers and views. `locale/fi/LC_MESSAGES/django.po`
has real Finnish translations; `locale/en/LC_MESSAGES/django.po` leaves
every `msgstr` empty since the source `msgid`s are already the English
strings (Django falls back to `msgid`, same effect as duplicating it, less
to keep in sync). Compiled `.mo` files aren't committed
(`locale/**/*.mo` is gitignored) -- `manage.py compilemessages` runs as a
deploy step, same pattern as `collectstatic`.

Worth stating plainly: today this only has visible effect inside Django
admin. The SPA never surfaces backend DRF error `detail` text -- every API
error in the frontend shows its own hardcoded `react-i18next` string
instead (e.g. `t("loanForm.error")`) -- so the serializer/view message
translations above are real and correct but currently unreachable from the
SPA's own UI. The model/admin-label translations are the part with actual
visible impact right now.
