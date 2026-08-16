"""Assertions about kava_varasto.settings.prod.

The suite runs under the dev settings, so these import the production module
directly rather than going through django.conf.settings. Reload is needed
because an earlier import (in another test or by the deploy checks) would
otherwise hand back a module built from different environment variables.

These assert on the settings dict rather than on behaviour on purpose:
override_settings can't reach DRF's prod-only knobs, because APIView binds
renderer_classes/permission_classes from api_settings at class-definition
time -- an overridden REST_FRAMEWORK leaves those class attributes as they
were imported, so a behavioural test here would pass while asserting nothing.
"""

import importlib
import sys

import pytest


@pytest.fixture
def prod(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-only-not-a-real-secret")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com")
    monkeypatch.delenv("DJANGO_NUM_PROXIES", raising=False)
    yield importlib.reload(importlib.import_module("kava_varasto.settings.prod"))
    # Leave no module built from this test's environment behind.
    sys.modules.pop("kava_varasto.settings.prod", None)


def test_browsable_api_is_off(prod):
    # An HTML console (and an HTML 403 naming the endpoint) served to anyone
    # sending Accept: text/html, with no consumer -- the SPA speaks JSON.
    assert prod.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] == [
        "rest_framework.renderers.JSONRenderer"
    ]


def test_login_throttle_survives_the_prod_override(prod):
    # REST_FRAMEWORK is rebuilt here; the base settings must come along.
    assert prod.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] == {"login": "10/min"}
    assert prod.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] == [
        "kava_varasto.accounts.permissions.IsAuthenticatedAndPasswordCurrent"
    ]


def test_num_proxies_defaults_to_one(prod):
    assert prod.REST_FRAMEWORK["NUM_PROXIES"] == 1


def test_num_proxies_is_configurable(monkeypatch, prod):
    monkeypatch.setenv("DJANGO_NUM_PROXIES", "2")

    reloaded = importlib.reload(prod)

    assert reloaded.REST_FRAMEWORK["NUM_PROXIES"] == 2


def test_prod_keeps_every_base_rest_framework_key(prod):
    # The override is written as a spread of base's dict. Replace it with a
    # plain dict and DRF falls back to its own defaults -- DEFAULT_PERMISSION_
    # CLASSES becomes AllowAny and the whole API goes anonymous, with every
    # other test still green.
    from kava_varasto.settings import base

    assert set(base.REST_FRAMEWORK) <= set(prod.REST_FRAMEWORK)
