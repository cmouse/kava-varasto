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
`LoanCreateSerializer.validate_items()` enforces, and what the picker
(`GET /api/loans/loanable-equipment/`, `kava_varasto.loans.views
.LoanableEquipmentListView`) shows so staff see real availability, not just
`available_quantity` (which ignores other active loans). This lives in the
`loans` app, not `inventory`, since it's loan data.

This is a check-then-act validation with no row locking -- two staff
creating loans for the same last-remaining item at the same instant could
both pass validation. Accepted for this app's scale (few users, a single
non-profit's gear closet).

The read-only Storage view (`Storage.jsx` / `GET /api/inventory/equipment/`)
still shows no "out" column -- that scope decision is unchanged; only loan
creation accounts for other active loans.
