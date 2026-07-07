from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-only-change-me")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])
