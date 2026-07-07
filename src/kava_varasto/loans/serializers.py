from django.db.models import F, Sum
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from kava_varasto.inventory.models import Equipment

from .models import Loan, LoanItem


def outstanding_quantity(equipment):
    total = LoanItem.objects.filter(equipment=equipment).aggregate(
        out=Sum(F("quantity") - F("quantity_returned"))
    )["out"]
    return total or 0


class LoanItemWriteSerializer(serializers.Serializer):
    equipment = serializers.PrimaryKeyRelatedField(queryset=Equipment.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class LoanItemReadSerializer(serializers.ModelSerializer):
    equipment = serializers.StringRelatedField()

    class Meta:
        model = LoanItem
        fields = ["equipment", "quantity", "quantity_returned"]


class LoanSerializer(serializers.ModelSerializer):
    items = LoanItemReadSerializer(many=True, read_only=True)
    responsible = serializers.StringRelatedField()
    returned_by = serializers.StringRelatedField()

    class Meta:
        model = Loan
        fields = [
            "id",
            "borrower_name",
            "borrower_phone",
            "due_date",
            "details",
            "responsible",
            "returned_by",
            "returned_at",
            "created_at",
            "items",
        ]


class LoanCreateSerializer(serializers.ModelSerializer):
    items = LoanItemWriteSerializer(many=True)

    class Meta:
        model = Loan
        fields = ["borrower_name", "borrower_phone", "due_date", "details", "items"]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError(_("At least one item is required."))
        equipment_ids = [item["equipment"].pk for item in items]
        if len(equipment_ids) != len(set(equipment_ids)):
            raise serializers.ValidationError(_("Each piece of equipment can only appear once per loan."))
        errors = []
        for item in items:
            equipment = item["equipment"]
            loanable = equipment.available_quantity - outstanding_quantity(equipment)
            if item["quantity"] > loanable:
                errors.append(
                    _("Only %(loanable)d of %(name)s available to loan right now.")
                    % {"loanable": loanable, "name": str(equipment)}
                )
        if errors:
            raise serializers.ValidationError(errors)
        return items

    def create(self, validated_data):
        items = validated_data.pop("items")
        loan = Loan.objects.create(responsible=self.context["request"].user, **validated_data)
        LoanItem.objects.bulk_create(LoanItem(loan=loan, **item) for item in items)
        return loan


class LoanableEquipmentSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    loanable_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Equipment
        fields = ["id", "name", "short_code", "category", "loanable_quantity"]
