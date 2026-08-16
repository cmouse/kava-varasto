from django.apps import AppConfig
from django.core.checks import register


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kava_varasto.accounts'
    label = 'accounts'

    def ready(self):
        from .checks import check_login_throttle_cache

        register(check_login_throttle_cache)
