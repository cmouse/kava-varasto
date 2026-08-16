import pytest
from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.test import override_settings

from kava_varasto.accounts.checks import DUMMY_BACKEND, check_login_throttle_cache


def test_no_error_with_the_configured_cache():
    assert check_login_throttle_cache(None) == []


@override_settings(CACHES={"default": {"BACKEND": DUMMY_BACKEND}})
def test_dummy_cache_is_an_error():
    (error,) = check_login_throttle_cache(None)

    assert error.id == "accounts.E001"


@override_settings(CACHES={"default": {"BACKEND": DUMMY_BACKEND}})
def test_the_check_is_registered():
    # Registration is the whole point: CI runs `manage.py check --deploy`, and
    # a check nobody wired up would pass every deploy in silence.
    with pytest.raises(SystemCheckError, match="accounts.E001"):
        call_command("check")
