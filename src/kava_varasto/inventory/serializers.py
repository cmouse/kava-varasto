from rest_framework import serializers

from .models import Equipment


class EquipmentSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = [
            "id",
            "name",
            "short_code",
            "category",
            "quantity",
            "broken_quantity",
            "available_quantity",
            "is_external_loanable",
            "image",
        ]

    def get_image(self, obj):
        # Relative URL: MEDIA_URL already carries the sub-path prefix, and a
        # request-absolute URL would be fragile behind the reverse proxy.
        return obj.image.image.url if obj.image else None
