import re

# Finnish phone number: a +358 international prefix or a local 0 prefix.
# Shared by kava_varasto.accounts.models.User.phone and
# kava_varasto.loans.models.Loan.borrower_phone -- both a loan's borrower and
# a staff member's own profile use the same format.
PHONE_RE = re.compile(r"^(\+358\d{6,12}|0\d{6,12})$")

# \ufeff (zero-width no-break space / BOM) added explicitly alongside \s:
# it's whitespace under JavaScript's \s -- and so under
# frontend/src/utils/phonePattern.js's native <input pattern> match -- but
# Python's str.isspace()/str.split() don't treat it as whitespace, which
# would otherwise let the frontend accept a value the API then rejects.
_WHITESPACE_RE = re.compile(r"[\s\ufeff]+")


def normalize_phone(value):
    """Strip whitespace (spaces, tabs, NBSP, U+FEFF, ...) out of a phone number.

    People type numbers in a readable grouping ("040 123 4567"); PHONE_RE
    has no whitespace in it, so callers must normalize before matching and
    store the normalized value, not the raw input. See _WHITESPACE_RE for
    why U+FEFF gets the same treatment as ordinary whitespace here.
    """
    return _WHITESPACE_RE.sub("", value)
