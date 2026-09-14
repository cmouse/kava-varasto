from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from kava_varasto.validators import PHONE_RE


class User(AbstractUser):
    must_change_password = models.BooleanField(
        _("must change password"),
        default=False,
        help_text=_(
            "Forces the user to change their password on next login. Set "
            "automatically when an admin creates the account or resets its password."
        ),
    )
    phone = models.CharField(
        _("phone"),
        max_length=30,
        blank=True,
        validators=[
            RegexValidator(
                PHONE_RE,
                _("Enter a valid phone number, e.g. 0401234567 or +358401234567."),
            )
        ],
    )
