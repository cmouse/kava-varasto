"""
ASGI config for kava_varasto project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kava_varasto.settings")

application = get_asgi_application()
