import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError

from kava_varasto.inventory.models import Category, Equipment, StorageLocation


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
def test_storage_location_str_is_name():
    location = StorageLocation.objects.get(name="Kolo")
    assert str(location) == "Kolo"


@pytest.mark.django_db
def test_storage_location_name_unique():
    StorageLocation.objects.create(name="Trailer")
    with pytest.raises(IntegrityError):
        StorageLocation.objects.create(name="Trailer")


@pytest.mark.django_db
def test_storage_location_ordered_by_name():
    StorageLocation.objects.create(name="Trailer")
    StorageLocation.objects.create(name="Attic")
    StorageLocation.objects.get(name="Kolo")
    names = list(StorageLocation.objects.values_list("name", flat=True))
    assert names == ["Attic", "Kolo", "Trailer"]


@pytest.mark.django_db
def test_storage_location_protected_while_equipment_exists():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    Equipment.objects.create(name="Dome tent", category=category, location=location)
    with pytest.raises(ProtectedError):
        location.delete()


@pytest.mark.django_db
def test_kolo_seeded_by_migration():
    # The 0007 migration's RunPython seeds "Kolo" via get_or_create, both for
    # existing rows (backfill) and for a fresh database. pytest-django builds
    # the test DB by running migrations, so this holds here -- it goes
    # vacuous under --no-migrations, which builds the schema directly instead.
    assert StorageLocation.objects.filter(name="Kolo").exists()


@pytest.mark.django_db
def test_equipment_str_includes_short_code():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    equipment = Equipment.objects.create(name="Dome tent", short_code="X75", category=category, location=location)
    assert str(equipment) == "X75 Dome tent"


@pytest.mark.django_db
def test_equipment_str_without_short_code_is_name_only():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    equipment = Equipment.objects.create(name="Dome tent", category=category, location=location)
    assert str(equipment) == "Dome tent"


@pytest.mark.django_db
def test_equipment_defaults():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    equipment = Equipment.objects.create(name="Dome tent", category=category, location=location)
    assert equipment.quantity == 1
    assert equipment.is_external_loanable is False


@pytest.mark.django_db
def test_equipment_multiple_without_short_code_allowed():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    Equipment.objects.create(name="Dome tent", category=category, location=location)
    Equipment.objects.create(name="Pop-up tent", category=category, location=location)


@pytest.mark.django_db
def test_equipment_short_code_unique_when_set():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    Equipment.objects.create(name="Dome tent", short_code="X75", category=category, location=location)
    with pytest.raises(IntegrityError):
        Equipment.objects.create(name="Another tent", short_code="X75", category=category, location=location)


@pytest.mark.django_db
def test_category_protected_while_equipment_exists():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    Equipment.objects.create(name="Dome tent", category=category, location=location)
    with pytest.raises(ProtectedError):
        category.delete()


@pytest.mark.django_db
def test_equipment_without_short_code_can_track_bulk_quantity():
    # e.g. "Trangia stove" -- no individual codes, just a stock count.
    category = Category.objects.create(name="Cooking")
    location = StorageLocation.objects.get(name="Kolo")
    equipment = Equipment.objects.create(name="Trangia stove", quantity=5, category=category, location=location)
    assert equipment.quantity == 5


@pytest.mark.django_db
def test_equipment_short_code_requires_quantity_one_clean():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    equipment = Equipment(name="Dome tent", short_code="X75", quantity=2, category=category, location=location)
    with pytest.raises(ValidationError):
        equipment.full_clean()


@pytest.mark.django_db
def test_equipment_short_code_requires_quantity_one_db_constraint():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    with pytest.raises(IntegrityError):
        Equipment.objects.create(name="Dome tent", short_code="X75", quantity=2, category=category, location=location)


@pytest.mark.django_db
def test_equipment_broken_quantity_defaults_to_zero():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    equipment = Equipment.objects.create(name="Dome tent", short_code="X75", category=category, location=location)
    assert equipment.broken_quantity == 0
    assert equipment.available_quantity == 1


@pytest.mark.django_db
def test_equipment_broken_quantity_reduces_available_quantity():
    category = Category.objects.create(name="Cooking")
    location = StorageLocation.objects.get(name="Kolo")
    equipment = Equipment.objects.create(
        name="Trangia stove", quantity=5, broken_quantity=2, category=category, location=location
    )
    assert equipment.available_quantity == 3


@pytest.mark.django_db
def test_equipment_broken_quantity_can_equal_quantity():
    category = Category.objects.create(name="Tents")
    location = StorageLocation.objects.get(name="Kolo")
    equipment = Equipment.objects.create(
        name="Dome tent", short_code="X75", broken_quantity=1, category=category, location=location
    )
    assert equipment.available_quantity == 0


@pytest.mark.django_db
def test_equipment_broken_quantity_over_quantity_rejected_by_clean():
    category = Category.objects.create(name="Cooking")
    location = StorageLocation.objects.get(name="Kolo")
    equipment = Equipment(name="Trangia stove", quantity=5, broken_quantity=6, category=category, location=location)
    with pytest.raises(ValidationError):
        equipment.full_clean()


@pytest.mark.django_db
def test_equipment_broken_quantity_over_quantity_rejected_by_db_constraint():
    category = Category.objects.create(name="Cooking")
    location = StorageLocation.objects.get(name="Kolo")
    with pytest.raises(IntegrityError):
        Equipment.objects.create(
            name="Trangia stove", quantity=5, broken_quantity=6, category=category, location=location
        )
