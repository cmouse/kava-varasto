import re

# Finnish phone number: a +358 international prefix or a local 0 prefix.
# Shared by kava_varasto.accounts.models.User.phone and
# kava_varasto.loans.models.Loan.borrower_phone -- both a loan's borrower and
# a staff member's own profile use the same format.
PHONE_RE = re.compile(r"^(\+358\d{6,12}|0\d{6,12})$")
