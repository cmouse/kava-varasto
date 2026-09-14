from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

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
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Write path for a user editing their own profile.

    Deliberately not UserSerializer: that one is also used read-only for
    /me/ and /login/ and carries is_staff/must_change_password, which a user
    must never be able to set on themselves via this endpoint.
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]


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
