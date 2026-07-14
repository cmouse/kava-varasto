from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from kava_varasto.inventory.models import Equipment

from .models import PHONE_RE, Loan, LoanItem

MAX_LOAN_ITEMS = 100


class LoanItemWriteSerializer(serializers.Serializer):
    equipment = serializers.PrimaryKeyRelatedField(queryset=Equipment.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class LoanItemReadSerializer(serializers.ModelSerializer):
    equipment = serializers.StringRelatedField()
    category = serializers.CharField(source="equipment.category.name", read_only=True)

    class Meta:
        model = LoanItem
        fields = ["id", "equipment", "category", "quantity", "quantity_returned", "quantity_broken"]


class LoanSerializer(serializers.ModelSerializer):
    items = LoanItemReadSerializer(many=True, read_only=True)
    responsible = serializers.StringRelatedField()
    returned_by = serializers.StringRelatedField()
    is_overdue = serializers.SerializerMethodField()

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
            "is_returned",
            "is_overdue",
            "items",
        ]

    def get_is_overdue(self, obj):
        # Server-side so the SPA never re-implements the local-date compare;
        # due today is not yet overdue, matching validate_due_date below.
        return not obj.is_returned and obj.due_date < timezone.localdate()


class LoanCreateSerializer(serializers.ModelSerializer):
    items = LoanItemWriteSerializer(many=True)

    class Meta:
        model = Loan
        fields = ["borrower_name", "borrower_phone", "due_date", "details", "items"]

    def validate_borrower_name(self, value):
        if len(value.split()) < 2:
            raise serializers.ValidationError(_("Enter both first and last name."))
        return value

    def validate_borrower_phone(self, value):
        if not PHONE_RE.match(value):
            raise serializers.ValidationError(
                _("Enter a valid phone number, e.g. 0401234567 or +358401234567.")
            )
        return value

    def validate_due_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError(_("Due date cannot be in the past."))
        return value

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError(_("At least one item is required."))
        if len(items) > MAX_LOAN_ITEMS:
            raise serializers.ValidationError(_("Too many items in a single loan."))
        equipment_ids = [item["equipment"].pk for item in items]
        if len(equipment_ids) != len(set(equipment_ids)):
            raise serializers.ValidationError(_("Each piece of equipment can only appear once per loan."))
        outstanding = {
            row["equipment_id"]: row["out"]
            for row in LoanItem.objects.filter(equipment_id__in=equipment_ids)
            .values("equipment_id")
            .annotate(out=Sum(F("quantity") - F("quantity_returned")))
        }
        errors = []
        for item in items:
            equipment = item["equipment"]
            loanable = equipment.available_quantity - (outstanding.get(equipment.pk) or 0)
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
        with transaction.atomic():
            loan = Loan.objects.create(responsible=self.context["request"].user, **validated_data)
            LoanItem.objects.bulk_create(LoanItem(loan=loan, **item) for item in items)
        return loan


class LoanReturnItemSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=LoanItem.objects.all())
    quantity_returned = serializers.IntegerField(min_value=0)
    quantity_broken = serializers.IntegerField(min_value=0, required=False)


class LoanReturnSerializer(serializers.Serializer):
    items = LoanReturnItemSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError(_("At least one item is required."))
        loan = self.context["loan"]
        item_ids = [entry["item"].pk for entry in items]
        if len(item_ids) != len(set(item_ids)):
            raise serializers.ValidationError(_("Each loan item can only appear once per return."))
        errors = []
        for entry in items:
            loan_item = entry["item"]
            new_quantity = entry["quantity_returned"]
            new_broken = entry.get("quantity_broken", loan_item.quantity_broken)
            entry["quantity_broken"] = new_broken
            if loan_item.loan_id != loan.pk:
                errors.append(_("Item %(id)d does not belong to this loan.") % {"id": loan_item.pk})
            elif new_quantity < loan_item.quantity_returned:
                errors.append(
                    _("Returned quantity for %(name)s cannot decrease.") % {"name": str(loan_item.equipment)}
                )
            elif new_quantity > loan_item.quantity:
                errors.append(
                    _("Returned quantity for %(name)s cannot exceed %(quantity)d.")
                    % {"name": str(loan_item.equipment), "quantity": loan_item.quantity}
                )
            elif new_broken < loan_item.quantity_broken:
                errors.append(
                    _("Broken quantity for %(name)s cannot decrease.") % {"name": str(loan_item.equipment)}
                )
            elif new_broken > new_quantity:
                errors.append(
                    _("Broken quantity for %(name)s cannot exceed returned quantity %(quantity)d.")
                    % {"name": str(loan_item.equipment), "quantity": new_quantity}
                )
        if errors:
            raise serializers.ValidationError(errors)
        return items

    def save(self):
        for entry in self.validated_data["items"]:
            loan_item = entry["item"]
            new_broken = entry["quantity_broken"]
            broken_delta = new_broken - loan_item.quantity_broken
            loan_item.quantity_returned = entry["quantity_returned"]
            loan_item.quantity_broken = new_broken
            loan_item.save(update_fields=["quantity_returned", "quantity_broken"])
            if broken_delta:
                Equipment.objects.filter(pk=loan_item.equipment_id).update(
                    broken_quantity=F("broken_quantity") + broken_delta
                )
        self.context["loan"].mark_returned_if_complete(self.context["request"].user)


class LoanableEquipmentSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    category_id = serializers.PrimaryKeyRelatedField(source="category", read_only=True)
    loanable_quantity = serializers.IntegerField(read_only=True)
    active_loan_ids = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = [
            "id",
            "name",
            "short_code",
            "category",
            "category_id",
            "quantity",
            "broken_quantity",
            "available_quantity",
            "is_external_loanable",
            "loanable_quantity",
            "active_loan_ids",
            "image",
        ]

    def get_image(self, obj):
        # Relative URL: MEDIA_URL already carries the sub-path prefix, and a
        # request-absolute URL would be fragile behind the reverse proxy.
        return obj.image.image.url if obj.image else None

    def get_active_loan_ids(self, obj):
        # Populated by the Prefetch(to_attr="active_loan_items") in
        # LoanableEquipmentListView; loans with this equipment still out.
        return sorted({item.loan_id for item in getattr(obj, "active_loan_items", [])})
