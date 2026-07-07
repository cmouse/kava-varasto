from rest_framework import serializers

from .models import Equipment


class EquipmentSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

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
        ]
