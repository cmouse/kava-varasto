import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from kava_varasto.inventory.models import Category, Equipment


@pytest.mark.django_db
def test_category_str_is_name():
    category = Category.objects.create(name="Tents")
    assert str(category) == "Tents"


@pytest.mark.django_db
def test_category_name_unique():
    Category.objects.create(name="Tents")
    with pytest.raises(IntegrityError):
        Category.objects.create(name="Tents")


@pytest.mark.django_db
def test_equipment_str_includes_short_code():
    category = Category.objects.create(name="Tents")
    equipment = Equipment.objects.create(name="Dome tent", short_code="X75", category=category)
    assert str(equipment) == "X75 Dome tent"


@pytest.mark.django_db
def test_equipment_str_without_short_code_is_name_only():
    category = Category.objects.create(name="Tents")
    equipment = Equipment.objects.create(name="Dome tent", category=category)
    assert str(equipment) == "Dome tent"


@pytest.mark.django_db
def test_equipment_defaults():
    category = Category.objects.create(name="Tents")
    equipment = Equipment.objects.create(name="Dome tent", category=category)
    assert equipment.quantity == 1
    assert equipment.is_external_loanable is False


@pytest.mark.django_db
def test_equipment_multiple_without_short_code_allowed():
    category = Category.objects.create(name="Tents")
    Equipment.objects.create(name="Dome tent", category=category)
    Equipment.objects.create(name="Pop-up tent", category=category)


@pytest.mark.django_db
def test_equipment_short_code_unique_when_set():
    category = Category.objects.create(name="Tents")
    Equipment.objects.create(name="Dome tent", short_code="X75", category=category)
    with pytest.raises(IntegrityError):
        Equipment.objects.create(name="Another tent", short_code="X75", category=category)


@pytest.mark.django_db
def test_category_protected_while_equipment_exists():
    category = Category.objects.create(name="Tents")
    Equipment.objects.create(name="Dome tent", category=category)
    with pytest.raises(ProtectedError):
        category.delete()
