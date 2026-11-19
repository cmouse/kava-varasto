from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from kava_varasto.validators import PHONE_RE, normalize_phone

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "is_staff",
            "must_change_password",
            "whats_new_seen_version",
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Write path for a user editing their own profile.

    Deliberately not UserSerializer: that one is also used read-only for
    /me/ and /login/ and carries is_staff/must_change_password, which a user
    must never be able to set on themselves via this endpoint.
    """

    # Declared explicitly (not model-derived) so the RegexValidator copied
    # from User.phone doesn't reject whitespace before validate_phone can
    # normalize it. allow_blank/required=False are re-supplied by hand to
    # match User.phone's blank=True -- a plain CharField() would 400 on
    # phone: "" and a user could never clear a number they'd previously set.
    # No max_length either -- see LoanCreateSerializer.borrower_phone for
    # why (the raw, unnormalized value can exceed it on interior
    # whitespace alone; PHONE_RE already caps the normalized value).
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]

    def validate_phone(self, value):
        if not value:
            return value
        value = normalize_phone(value)
        if not PHONE_RE.match(value):
            raise serializers.ValidationError(
                _("Enter a valid phone number, e.g. 0401234567 or +358401234567.")
            )
        return value


class UserContactSerializer(serializers.ModelSerializer):
    """Read-only contact card for a staff member, nested onto a Loan.

    Used for Loan.responsible/returned_by (see loans.serializers.LoanSerializer)
    so the SPA can show who handed out or accepted back a loan without a
    second round-trip. Every field here is visible to any authenticated user
    -- the app has one trust tier already (borrower phone numbers sit on
    every loan row the same way), so this isn't a new exposure.
    """

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "phone"]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.context["request"].user)
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        return user
