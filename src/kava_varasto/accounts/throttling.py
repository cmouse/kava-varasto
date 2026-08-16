from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """Per-client-address cap on credential guesses.

    Neither DRF nor the Django admin rate-limits logins out of the box, and
    staff accounts are this app's only trust tier -- one guessed password is
    the whole ledger plus the admin.

    Not AnonRateThrottle, which keys on the same address but skips authenticated
    requests entirely (a valid session would then guess for free) and shares the
    global "anon" scope with every other unauthenticated endpoint.

    Behind a reverse proxy the address comes from X-Forwarded-For, which is
    client-supplied end to end. REST_FRAMEWORK["NUM_PROXIES"] (settings/prod.py)
    says how many entries at the end of that chain the deployment's own proxies
    appended, and DRF counts that one -- so the fix for spoofing is at the
    proxy, which must append the real address. See DESIGN.md.
    """

    scope = "login"

    def get_cache_key(self, request, view=None):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
