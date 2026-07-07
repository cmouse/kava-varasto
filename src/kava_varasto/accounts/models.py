from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    must_change_password = models.BooleanField(
        _("must change password"),
        default=False,
        help_text=_(
            "Forces the user to change their password on next login. Set "
            "automatically when an admin creates the account or resets its password."
        ),
    )
