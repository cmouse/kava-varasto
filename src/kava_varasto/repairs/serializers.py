from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from kava_varasto.inventory.models import Equipment

from .models import RepairTicket

MAX_TICKET_EQUIPMENT = 100


class TicketEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ["id", "name", "short_code"]


class RepairTicketSerializer(serializers.ModelSerializer):
    equipment = TicketEquipmentSerializer(many=True, read_only=True)
    reported_by = serializers.StringRelatedField()
    resolved_by = serializers.StringRelatedField()

    class Meta:
        model = RepairTicket
        fields = [
            "id",
            "title",
            "description",
            "equipment",
            "status",
            "is_open",
            "reported_by",
            "reported_at",
            "resolved_by",
            "resolved_at",
        ]


class RepairTicketWriteSerializer(serializers.ModelSerializer):
    equipment = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Equipment.objects.all(), required=False
    )

    class Meta:
        model = RepairTicket
        fields = ["title", "description", "equipment", "status"]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError(_("A title is required."))
        return value.strip()

    def validate_equipment(self, equipment):
        if len(equipment) > MAX_TICKET_EQUIPMENT:
            raise serializers.ValidationError(_("Too many pieces of equipment on a single ticket."))
        if len({item.pk for item in equipment}) != len(equipment):
            raise serializers.ValidationError(_("Each piece of equipment can only be tagged once."))
        return equipment

    def create(self, validated_data):
        equipment = validated_data.pop("equipment", [])
        status = validated_data.pop("status", None)
        user = self.context["request"].user
        with transaction.atomic():
            ticket = RepairTicket(reported_by=user, **validated_data)
            if status is not None:
                ticket.set_status(status, user)
            ticket.save()
            ticket.equipment.set(equipment)
        return ticket

    def update(self, instance, validated_data):
        equipment = validated_data.pop("equipment", None)
        status = validated_data.pop("status", None)
        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(instance, field, value)
            if status is not None:
                # Never stamps resolved_at/resolved_by here: set_status() is
                # the one place that knows the bookkeeping, so the API and the
                # admin behave identically.
                instance.set_status(status, self.context["request"].user)
            instance.save()
            if equipment is not None:
                instance.equipment.set(equipment)
        return instance
