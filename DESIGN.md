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
by `Equipment.clean()` and a DB check constraint. Loan returns can also
increment this per equipment (see "Loan check-in / return" below) when
returned items come back damaged.

Repair work queue
-----------------

Gear breaks, and gear needs upkeep. Issue #36 asks for a way to report and
handle both, so `kava_varasto.repairs.RepairTicket` is a free-text piece of
work -- "X75 pole bent" as much as "sharpen all them axes" -- with a status
(`open`, `in progress`, `done`, `won't fix`), the member who reported it, and
whoever eventually closed it.

Equipment tagging is a `ManyToManyField` and optional in both directions: a
ticket can name one item, several, or none at all. A maintenance chore covering
six axes is one ticket tagging six items, not six tickets, and "service the
trailer" is a perfectly good ticket that tags nothing. The title always has to
stand on its own -- the tags are a convenience for finding related work, not
the subject of the ticket.

The queue is deliberately **not** wired to `Equipment.broken_quantity`. Filing
a ticket doesn't mark stock broken and resolving one doesn't make it loanable
again; the count stays what it was, maintained by staff in the Django admin
(`EquipmentAdmin.list_editable`). The two answer different questions -- the
ticket says *what needs doing and by whom*, the field says *how many can't go
out right now* -- and a chore like sharpening axes has no bearing on
availability at all. Keeping them independent means the loan availability
calculations (`available_quantity`, `loanable_quantity`,
`LoanCreateSerializer.validate_items`) are untouched by this feature, and no
double-counting seam exists between a damaged loan return and a repair ticket
filed for the same damage. `tests/test_repairs_api.py` asserts the
independence directly.

Resolution bookkeeping lives in one place: `RepairTicket.set_status(status,
by_user)`, modelled on `Loan.mark_returned_if_complete()`. Moving into a
closed status stamps `resolved_at`/`resolved_by`, moving back out clears them,
and a no-op status write leaves the original resolver alone. A DB check
constraint (`repairticket_resolution_matches_status`) enforces the pairing, so
the stamping cannot be skipped -- which is why the admin goes through the same
method via a form `clean()` rather than through `save_model()`: the model's
`full_clean()` runs during form validation, before `save_model()` would get a
chance to fix anything up. The constraint hardcodes the status literals into
its SQL, so adding a fifth status needs a migration that rewrites it, not just
an edit to `TicketStatus`.

Any logged-in user can file, edit, close and delete tickets -- the same trust
level the loan endpoints already assume, no `is_staff` gate. `GET
/api/repairs/` returns only open tickets, since the queue is a to-do list;
`?status=all` or an explicit `?status=done` digs up history, and an
unrecognised value is a 400 rather than a silently empty list.

The whole feature is one SPA page (`frontend/src/pages/Repairs.jsx`, tab
"Repairs"/"Korjaukset"). A ticket is a line of text and a status, so there is
no detail page and no separate form page: the status dropdown PATCHes straight
from the list row, the description shows inline under the title, and reporting
is a collapsible form at the top of the same page. Tagging equipment reuses
`useEquipmentFilter` through `EquipmentTagPicker` -- a search box plus chips,
not the full `EquipmentFilterBar`, whose category and location controls are
more machinery than tagging needs.

Categorization
--------------
To make it easier to find equipment, there should be categories of equipment when borrowing, so that equipment with no short code is discoverable.

Storage locations
------------------

Equipment records not just what and how much, but also *where* it physically
lives (issue #31): the club's gear isn't all in one room -- most of it sits in
"Kolo" (the troop's clubhouse), the rest in a container, an attic, or a
trailer. `StorageLocation` (`kava_varasto.inventory.models.StorageLocation`)
is a lookup table with the same shape as `Category`: unique `name`,
`ordering = ["name"]`, `__str__` returning the name, registered in admin with
`list_display`/`search_fields = ["name"]`. `Equipment.location` is a
non-nullable FK to it with `on_delete=PROTECT`, `related_name="equipment"`.

A lookup table rather than a free-form `CharField` or `TextChoices` (the
`Category` precedent -- the repo has zero `choices=`/`TextChoices` anywhere):
locations are club facts that change without a deploy (a new container, a
member's garage), and a free-form field would spawn "Kolo"/"kolo"/"KOLO"
duplicates that no dropdown can group. `unique=True` on `name` enforces that,
and `PROTECT` means deleting a location in use is refused rather than quietly
orphaning gear.

**No `default=` on the FK.** A hardcoded `default=1` breaks on a fresh
database (nothing guarantees row 1 is Kolo), and a callable default would run
a DB query on every `Equipment()` instantiation. "Default to Kolo" is instead
delivered by two separate, deliberate mechanisms, one per way a row gets a
location:

- *existing rows*, at migration time: `inventory/migrations/
  0007_storagelocation.py` adds `location` as nullable, backfills every
  existing `Equipment` row to a `StorageLocation` named `"Kolo"` via
  `get_or_create` (the literal string, matching the model's
  `DEFAULT_LOCATION_NAME` constant -- migrations must not import from the
  live models module), then tightens the field to non-null in a final
  `AlterField`. The same `get_or_create` also seeds Kolo on a **fresh**
  database, so a brand-new install has a working default with no fixture
  step.
- *new rows*, in the admin: `EquipmentAdmin.get_changeform_initial_data`
  looks up the Kolo row and preselects it on the "add equipment" form, so
  staff only need to change it when the item genuinely lives elsewhere.
  Falls back to no initial value (not a 500) if Kolo has been renamed or
  deleted.

Equipment is created/edited only through the Django admin (the SPA has no
equipment write path), so "dropdown" for issue #31 means the admin
change-form's FK select -- `EquipmentAdmin` declares no explicit `fields`, so
`location` appears there automatically, same as `category` and `image`
already did. `location` is also added to `EquipmentAdmin.list_display` and
`list_filter`. The SPA side is display and filtering only: both equipment
serializers carry the field (`EquipmentSerializer.location` as a
`StringRelatedField`; `LoanableEquipmentSerializer.location`/`location_id`,
mirroring the existing `category`/`category_id` pair so a filter can key off
a stable id), and both querysets' `select_related(...)` include `"location"`
to avoid a query per row. `Storage.jsx` shows a Location column and filters
by it via a `<select>` dropdown in `EquipmentFilterBar.jsx` (deliberately a
dropdown, not a second row of pill buttons -- category pills plus location
pills would crowd the mobile layout, and a dropdown is what issue #31 asks
for); `EquipmentDetailModal.jsx` shows it next to Category. Both live off
`useEquipmentFilter.js`'s existing `categories`-style deduping pattern,
reused for `locations`.

Listings
--------
All borrows need to be listable as active and old.

Loans
-----

A loan (`kava_varasto.loans.models.Loan`) records one borrower taking out
equipment: freeform `borrower_name` and `borrower_phone` (so the borrower can
be reached -- borrowers never have `User` accounts, see "Borrower name/phone
autofill"), a `due_date`, and a freeform `details` field. Each piece of
equipment on the loan is a `LoanItem` (equipment FK + quantity), so a loan
can cover several pieces of equipment at once; the same equipment can appear
only once per loan (`loanitem_unique_loan_equipment` DB constraint, also
validated by `LoanCreateSerializer`).

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
exceeds what's actually free right now. The `Loan` and its `LoanItem` rows
are created inside one `transaction.atomic()` block, so a failure can't
leave a half-created loan behind.

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

The endpoint also reports `active_loan_ids` per equipment: ids of
non-returned loans on which the equipment is still out (a filtered
`Prefetch` on `loan_items` -- `loan.returned_at IS NULL` and
`quantity_returned < quantity`, so an item already fully handed back
on a still-open loan doesn't count). The Storage view renders these
as `#nnn` links to the loan detail page (`/loans/:id`), and lays the
table out like the loan detail items table: one table, a
`table-group-divider` `<tbody>` per category with a header row
(shared `groupByCategory` helper in `frontend/src/utils/`, also used
by the new-loan equipment picker). Grouping happens after the
client-side search/category filter, so filtered-out categories show
no header row.

Equipment detail view and images
--------------------------------

Photos live in their own model so one upload can serve many equipment
entries (e.g. ten identical Trangia stoves): `EquipmentImage` (`name`,
`image` -- an `ImageField(upload_to="equipment/")`, requires Pillow --
and `uploaded_at`). `Equipment.image` is a nullable FK to it with
`on_delete=SET_NULL`, so deleting a shared photo just reverts the
equipment to "no image". Staff upload photos in the `EquipmentImage`
admin (list shows a thumbnail preview) and pick one on the Equipment
change form via the FK select (plus the inline "+" popup);
`EquipmentAdmin` declares no explicit `fields`, so the field appears
there automatically. Migration `inventory/0006` converted the previous
direct `ImageField` on `Equipment`: existing file paths became
`EquipmentImage` rows (deduplicated by path), files stayed in place
under `media/equipment/`.

The API serializers (`EquipmentSerializer` and
`LoanableEquipmentSerializer`) expose the image as a *relative* URL via
a `SerializerMethodField` (`obj.image.image.url` or `null`) rather than DRF's
default request-absolute URL: `MEDIA_URL = f"{SCRIPT_NAME}/media/"`
already bakes in the sub-path prefix, and an absolute URL would be
fragile behind the reverse proxy. The SPA uses the value as-is -- never
prepend the mount point (`frontend/src/utils/scriptName.js`) or hardcode
`/media/`.

Clicking an equipment row on the Storage view opens
`frontend/src/components/EquipmentDetailModal.jsx`: the image (or a
"no image" placeholder) plus code, category, quantities, external-loanable
badge and active-loan links. It is a React-controlled modal (conditional
render of Bootstrap's modal markup with a manual backdrop, Escape and
backdrop-click close) -- Bootstrap's Modal JS mutates the DOM
imperatively and fights React, so it isn't used. Rows keep their native
table semantics (no `role="button"` -- that would strip the row role for
screen readers); they are made interactive with `tabIndex`,
Enter/Space handling and a pointer cursor, and the row click handler
ignores clicks that land on the active-loan `<a>` links so those still
navigate.

In production the reverse proxy serves `MEDIA_ROOT` at `media/`; in dev
`urls.py` appends `static(settings.MEDIA_URL, ...)` when `DEBUG` (the
SPA catch-all already excludes `media/`).

Loan overview page
-------------------

Staff view loans via the SPA (`frontend/src/pages/LoanList.jsx`,
`GET /api/loans/` -- the same URL as loan creation, `POST`; DRF's
`ListCreateAPIView` dispatches by method), split into active (not yet
fully returned) and returned/historical sections client-side using the
`is_returned` field on `LoanSerializer`. Rows no longer inline each
loan's items (that broke down for loans with many items) -- instead
each row shows an item count and the loan ID links to the loan detail
page.

`LoanSerializer` also exposes `is_overdue` (active and
`due_date < timezone.localdate()` -- due today is not yet overdue,
matching the create-time validation). It is computed server-side so the
SPA never re-implements the Helsinki-timezone date compare. The list
and detail pages render a red warning triangle next to an overdue due
date via `frontend/src/components/OverdueIcon.jsx`, an inlined
Bootstrap Icons SVG (the project ships no icon library) with tooltip
and aria-label from the `loanList.overdue` i18n key.

The main list no longer shows the full loan history: the list endpoint
filters server-side (`LoanListCreateView.get_queryset`) so the default
response contains every active loan plus loans returned within the
last ~2 months (`ARCHIVE_AFTER = timedelta(days=61)`, compared against
`returned_at`). Older returned loans are reachable via
`GET /api/loans/?archived=true` and shown on a separate archive page
(`frontend/src/pages/LoanArchive.jsx` at `/loans/archive`, linked from
the navbar). Active loans never move to the archive regardless of age
-- the cutoff only applies to `returned_at`. Both pages render the
returned-loans table through the shared
`frontend/src/components/ReturnedLoansTable.jsx` component, and the
archived query uses the react-query key `["loans", "archived"]`, which
the existing `["loans"]` mutation invalidations prefix-match.

Loan detail page
------------------

Clicking a loan ID anywhere in `LoanList.jsx` opens
`frontend/src/pages/LoanDetail.jsx` at `/loans/:id`, backed by
`GET /api/loans/<pk>/` (`kava_varasto.loans.views.LoanDetailView`, a
`RetrieveAPIView` reusing `LoanSerializer` and the same
`prefetch_related("items__equipment__category")` queryset as the list
view). It shows the loan's metadata (borrower, phone, due date,
responsible, details, created date, status, and returned-by/at once
returned) plus the loan's items grouped by equipment category: loan item
JSON includes a `category` name (`LoanItemReadSerializer`), and the page
renders one quantity/returned/broken table whose rows are grouped under
full-width category separator rows (one `<tbody>` per category, sorted
alphabetically), with a "Return" button linking to `/loans/:id/return`
for loans that aren't fully returned yet. An unknown ID returns a real 404 from the
API rather than a client-side lookup miss; `useLoan` (`frontend/src/api/
loans.js`) skips react-query's retries on 404 so the not-found message
shows immediately instead of after three doomed refetches.

Loan check-in / return
-----------------------

Each active loan on `LoanList.jsx` (and the loan detail page) has a
"Return" button (`frontend/src/pages/LoanReturn.jsx`, `/loans/:id/return`)
that posts to `POST /api/loans/<id>/return/`
(`kava_varasto.loans.views.LoanReturnView`). The page fetches the loan
via `useLoan(id)` (`GET /api/loans/<pk>/`) and shows one row per
`LoanItem`: for items not yet fully returned, two number inputs --
returned quantity (defaulting to full quantity) and broken quantity
(defaulting to the stored `quantity_broken`) -- or a "fully returned"
badge for items that are.

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

Each `LoanItem` also tracks `quantity_broken` -- how many of the returned
quantity came back damaged. It's an optional key per return-request item
(`{"item": <id>, "quantity_returned": <int>, "quantity_broken": <int>}`),
bounded the same way as `quantity_returned`: cannot decrease from what's
already stored, and cannot exceed the *new* `quantity_returned` in the same
request. If omitted, the existing stored value carries over unchanged --
it is never implicitly reset to 0, which would otherwise clobber a broken
count recorded in an earlier partial return. (`LoanReturn.jsx` always sends
it, prefilled with the stored value, so the omission case only matters for
direct API callers.)

Marking something broken updates `Equipment.broken_quantity` inside the
same `transaction.atomic()` block as the `quantity_returned` update: only
the *delta* between old and new `quantity_broken` is added, via
`Equipment.objects.filter(pk=...).update(broken_quantity=F("broken_quantity")
+ delta)` -- a single atomic SQL statement, so concurrent returns touching
the same equipment can't race into a lost update. This reuses the existing
`broken_quantity` field and `available_quantity`/`loanable_quantity`
computations unchanged -- no other code needed to change for damaged
returns to stop showing as available.

`LoanItem`'s own DB check constraint
(`loanitem_quantity_broken_lte_quantity_returned`) and `clean()` mirror
`loanitem_quantity_returned_lte_quantity` exactly. The Django admin's
`LoanItemInline` shows `quantity_broken` read-only -- editing it there
would bypass the `Equipment.broken_quantity` side effect, so the return
endpoint / `LoanReturn.jsx` is the only write path.

Scope note: broken can only be recorded for a `LoanItem` while it's still
being actively returned -- once an item is fully returned, `LoanReturn.jsx`
only shows a static badge and it drops out of the submitted payload, so
there's no UI path to retroactively mark an already-returned item broken
later. "Found broken after the fact" is covered from two directions instead:
the repair queue records the *work* that needs doing (see "Repair work
queue"), and staff adjust the *count* by editing `Equipment.broken_quantity`
in the Django admin.

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

These rules are enforced in the serializer (per-field API errors) and again
at the model level: `Loan.clean()` checks the two-word name, the phone
regex lives in a `RegexValidator` on `borrower_phone` (shared `PHONE_RE`
constant in `loans/models.py`), and the past-due-date check runs only on
creation (`self._state.adding`) so admin edits of loans whose due date has
since passed still save. `clean()` also requires `returned_at`/`returned_by`
to be set together. Two portable `CheckConstraint`s back this at the DB
level (`loan_borrower_name_has_space`, `loan_returned_fields_consistent`);
a phone-regex CHECK is skipped as it is not portable to SQLite and a
due-date CHECK is impossible (time-dependent). Admin forms run `clean()`
via ModelForm validation, so admin-created loans are validated too.
`LoanNew.jsx` mirrors the same rules
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
the per-page auth-guard pattern used elsewhere.

That gate is UX only -- a rendering decision the session can ignore by
calling the API directly -- so the flag is enforced server-side in two
places, one per way into the data:

- `IsAuthenticatedAndPasswordCurrent` (`accounts/permissions.py`) is the
  project's `DEFAULT_PERMISSION_CLASSES`, so every DRF view denies a flagged
  user with 403. `LoginView`/`CurrentUserView` (`AllowAny`) and
  `LogoutView`/`ChangePasswordView` (plain `IsAuthenticated`) are the
  deliberate exceptions: they are exactly the endpoints needed to clear the
  flag or get out.
- `ForcePasswordChangeMiddleware` (`accounts/middleware.py`) redirects a
  flagged session away from `/admin/` to the SPA's change-password screen,
  since the Django admin is a second complete way into the same data and
  knows nothing about the flag. Admin logout is exempt so a redirected user
  isn't stuck; the admin's own password-change form is not exempt, because
  it wouldn't clear the flag and would loop.

Without this an account would keep working access forever on the password
its issuing admin picked -- the flag would announce the debt without
collecting it.

Login rate limiting
-------------------

Neither DRF nor the Django admin throttles logins by default, and this app
has exactly one trust tier: a guessed staff password is the whole ledger
plus the admin. `LoginRateThrottle` (`accounts/throttling.py`) caps
credential guesses at `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login"]`
(10/min) per client address.

Both credential endpoints share that one counter, because they guess the
same passwords: DRF applies it to `LoginView` through `throttle_classes`,
and `AdminLoginThrottleMiddleware` applies the same class to `POST
/admin/login/`, which is a plain Django view DRF never sees, returning 429
with `Retry-After`.

Every attempt counts, successes included. Counting only failures would let
an attacker reset the budget by interleaving one valid login, and the cost
of counting all of them is that ten admin logins in a minute during a
debugging session cost a minute's wait.

Behind a proxy the client address comes from `X-Forwarded-For`, and the
whole header is client-supplied. `REST_FRAMEWORK["NUM_PROXIES"]`
(`DJANGO_NUM_PROXIES`, default 1) tells DRF how many entries at the *end*
of that chain its own proxies appended: at 1 it counts `addrs[-1]`, so
whatever the client prepended is ignored.

That only holds if the proxy really does append. DRF does not verify it --
if the proxy forwards the client's header untouched, `addrs[-1]` is a value
the client chose, and it can both mint a fresh bucket per guess and lock
out any address it names. **The proxy must set `X-Forwarded-For`**: Apache
mod_proxy appends by default, nginx does not (`proxy_set_header
X-Forwarded-For $proxy_add_x_forwarded_for;` -- see README.md). Set
`DJANGO_NUM_PROXIES` to the real number of appending hops if a CDN or a
second proxy is added; leaving it blank in `.env` is a boot failure, not a
default.

The counter lives in `CACHES["default"]`, deliberately `LocMemCache`: it is
per process, so N gunicorn workers mean an effective N x 10/min. That is a
bound where there was none, without a cache server to run or a new state
directory for the deploy rsync to protect. Swap in a shared backend if the
worker count ever makes the multiple matter.

Handing the mount point to the SPA
----------------------------------

`kava_varasto.views.spa` passes `request.META["SCRIPT_NAME"]` into
`templates/spa.html`, which renders it as `data-script-name` on the `#root`
div. `frontend/src/utils/scriptName.js` reads it once and exports it; the
three consumers are the axios `baseURL` (`api/client.js`), the router
`basename` (`App.jsx`) and the `/i18n/setlang/` form action
(`LanguageSwitcher.jsx`).

It used to be an inline `<script>` setting `window.SCRIPT_NAME`. A data
attribute instead, because a Content-Security-Policy would otherwise need a
`sha256-` allowance for that inline block -- and the hash covers the
interpolated prefix, so `/varasto` and a root-mounted deployment would need
different policies. Reading the value from the DOM keeps `script-src 'self'`
correct at every mount point, and `tests/test_spa.py` asserts the shell
carries no inline script at all so it cannot creep back.

The Vite dev server serves its own `frontend/index.html` with an empty
`data-script-name`, matching a root mount.

API renderers
-------------

`settings/prod.py` narrows `DEFAULT_RENDERER_CLASSES` to `JSONRenderer`.
DRF's default list also carries `BrowsableAPIRenderer`, which answers any
`Accept: text/html` request -- including an anonymous one -- with an HTML
API console naming the endpoint and offering its methods. The SPA speaks
only JSON, so in production that renderer has no consumer, just surface.
It stays enabled under the dev settings, where it is useful.

One consequence worth knowing when debugging production by hand: a request
asking for exactly `Accept: text/html` now gets 406, which masks the status
it would otherwise have returned (a 403 or a 404 reads as 406). Browsers and
`curl`'s default `*/*` are unaffected -- they negotiate to JSON.

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

SPA translations
------------------

The frontend has its own translation layer: `react-i18next` with bundled
JSON catalogs (`frontend/src/i18n/locales/{fi,en}.json`), Finnish as both
default and fallback language. The initial language comes from the `lang`
attribute on `templates/spa.html`'s `<html>` element, which Django's
`LocaleMiddleware` sets per request -- so the SPA and Django agree on the
active language. `LanguageSwitcher.jsx` (FI/EN buttons in the navbar) posts
to Django's stock `i18n/setlang/` view (`django.conf.urls.i18n`), which
stores the choice in the language cookie and reloads the page -- one
language state shared by the SPA, DRF, and the admin, instead of a separate
frontend-only preference.

Form field conventions
----------------------

Mandatory form fields are marked with a red asterisk via the `required`
class on the Bootstrap `form-label` (CSS `::after` rule in
`frontend/src/index.css`) -- purely visual, actual enforcement stays in the
inputs' `required` attributes and the serializers. Currently applied to the
loan forms (`LoanNew.jsx`, `LoanReturn.jsx`).

Deployment automation
---------------------

Deployments are driven by `.github/workflows/deploy.yml`, which reacts to the
`CI` workflow completing successfully (`workflow_run`) rather than to the
push itself: a red build cannot deploy, and the test suite is not run a
second time. `main` deploys to the `staging` environment, a `vX.Y.Z` tag to
`production` (which re-checks the tag against `pyproject.toml`'s version, as
`publish.yml` does).

Routing is a job of its own rather than an `if:` on each deploy job.
`workflow_run` exposes the triggering ref as `head_branch`, and for a tag
push that field is not dependable -- it may carry the tag name or the branch
the tagged commit happens to sit on, so keying production off it risks a tag
that silently deploys nowhere. The `target` job instead checks out the
commit with full history and asks `git tag --points-at HEAD`, which is
unambiguous. The cost is that any branch push at a tagged commit deploys to
production again -- the two pushes are the same commit, so nothing in git
tells them apart -- but it redeploys an identical tree, which is far
preferable to a release tag that silently deploys nowhere.

Each environment carries its own `HOST`, `USER` and `INSTALL_PATH`
variables and `SSH_KEY` secret. `INSTALL_PATH` has no default and is
rejected when empty (rsync with an empty destination would write to the
deploy user's home root) or when it starts with `~` (rsync's remote path is
expanded by a shell, but the restart step reads the path from a quoted
variable where the tilde stays literal, so a tilde would upload correctly
and then fail on `cd`).

A deploy does two things: rsync, then `systemctl --user restart
varasto@<environment>` -- a templated unit instance, so staging and
production run side by side on one host under `varasto@staging` and
`varasto@production`.
Everything else -- building the frontend, migrating, `collectstatic`,
`compilemessages` -- belongs to `start.sh`, which the unit runs on every
start. Duplicating those steps in the deploy would mean handing CI the
production `DJANGO_SECRET_KEY` and friends purely to repeat work the
service is about to do anyway. The one thing the deploy adds is a copy of
`varasto.sqlite3` before the restart, because that restart migrates and
migrations do not roll back.

The unit of deployment is the working tree, not the wheel that `publish.yml`
builds. `BASE_DIR` is derived from the repo root
(`src/kava_varasto/settings/base.py`), so `templates/`, `locale/`,
`staticfiles/`, `media/` and `varasto.sqlite3` must live next to `src/`; a
`pip install` of the wheel would relocate `BASE_DIR` into site-packages and
break all of them. The shared steps live in `.github/actions/deploy` (a
composite action, not a reusable workflow, because environment secrets only
resolve in the job that declares the `environment:`).

Two deliberate choices in that action:

- **rsync without `--delete`.** Excludes protect the receiver, but a single
  mistake in the exclude list would destroy `varasto.sqlite3`, `.env` or
  `media/` with no way back. The cost of omitting it is stale build output,
  which `start.sh` regenerates on the next start anyway.
- **A backup before every `migrate`.** Taken through sqlite3's backup API
  rather than `cp`, which is not safe against the WAL journal mode the app
  runs in.

Compiled translations (`locale/**/*.mo`) and the built frontend are
gitignored, so they never travel in the rsync -- `start.sh` produces both on
the host, which therefore needs Node and `gettext` alongside Python.
