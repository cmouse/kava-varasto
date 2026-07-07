import json

from django.conf import settings
from django.template import Library
from django.templatetags.static import static

register = Library()

MANIFEST_PATH = settings.STATICFILES_DIRS[0] / "frontend" / ".vite" / "manifest.json"

_manifest_cache = None


def _load_manifest():
    global _manifest_cache
    if settings.DEBUG or _manifest_cache is None:
        with open(MANIFEST_PATH) as f:
            _manifest_cache = json.load(f)
    return _manifest_cache


@register.simple_tag
def vite_asset(entry):
    """Hashed URL for a Vite build entry's JS file, e.g. vite_asset('index.html')."""
    return static("frontend/" + _load_manifest()[entry]["file"])


@register.simple_tag
def vite_css(entry):
    """Hashed URLs for a Vite build entry's CSS files."""
    return [static("frontend/" + css) for css in _load_manifest()[entry].get("css", [])]
