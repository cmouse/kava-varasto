"""
WSGI config for kava_varasto project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kava_varasto.settings")

application = get_wsgi_application()
