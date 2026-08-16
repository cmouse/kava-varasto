"""Assertions about kava_varasto.settings.prod.

The suite runs under the dev settings, so these import the production module
directly rather than going through django.conf.settings. Reload is needed
because an earlier import (in another test or by the deploy checks) would
otherwise hand back a module built from different environment variables.
"""

import importlib

import pytest


@pytest.fixture
def prod(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-only-not-a-real-secret")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com")
    monkeypatch.delenv("DJANGO_NUM_PROXIES", raising=False)
    return importlib.reload(importlib.import_module("kava_varasto.settings.prod"))


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
