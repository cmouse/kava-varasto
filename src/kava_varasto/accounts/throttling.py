from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """Per-client-address cap on credential guesses.

    Neither DRF nor the Django admin rate-limits logins out of the box, and
    staff accounts are this app's only trust tier -- one guessed password is
    the whole ledger plus the admin. Keyed on the address alone (not on the
    user, as AnonRateThrottle would be) because the callers being counted are
    unauthenticated by definition.

    Behind a reverse proxy the address comes from X-Forwarded-For, which is
    client-supplied: DRF only trusts it as far as REST_FRAMEWORK["NUM_PROXIES"]
    says it should (set in settings/prod.py), otherwise an attacker could mint
    a fresh bucket per request.
    """

    scope = "login"

    def get_cache_key(self, request, view=None):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
