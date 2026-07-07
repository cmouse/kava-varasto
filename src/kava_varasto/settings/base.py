"""
Django settings shared by all environments for kava_varasto project.
"""

from pathlib import Path

import environ

# src/kava_varasto/settings/base.py -> settings/ -> kava_varasto/ -> src/ -> repo root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

env = environ.Env()
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(str(_env_file))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "kava_varasto.accounts",
    "kava_varasto.inventory",
    "kava_varasto.loans",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "kava_varasto.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "kava_varasto.wsgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    ),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Helsinki"

USE_I18N = True

USE_TZ = True

STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Sub-path mounting -----------------------------------------------------
# This project must be relocatable to run under a URL prefix, e.g.
# http://webhost/varasto/, behind a reverse proxy that strips the prefix
# before forwarding the request (see README.md for the nginx recipe). One
# env var drives every setting that needs to know about the prefix, so they
# can never drift out of sync with each other.
SCRIPT_NAME = env("DJANGO_FORCE_SCRIPT_NAME", default="")
FORCE_SCRIPT_NAME = SCRIPT_NAME or None
STATIC_URL = f"{SCRIPT_NAME}/static/"
MEDIA_URL = f"{SCRIPT_NAME}/media/"

# Scope cookies to the mount point too, in case this host is ever shared
# with another application. Safe no-op default ("/") when SCRIPT_NAME="".
SESSION_COOKIE_PATH = SCRIPT_NAME or "/"
CSRF_COOKIE_PATH = SCRIPT_NAME or "/"
