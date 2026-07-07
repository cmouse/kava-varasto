import pytest

from kava_varasto.inventory.models import Category, Equipment


@pytest.mark.django_db
def test_equipment_list_requires_auth(client):
    response = client.get("/api/inventory/equipment/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_equipment_list_returns_stock_levels(admin_client):
    category = Category.objects.create(name="Cooking")
    Equipment.objects.create(name="Trangia stove", quantity=5, broken_quantity=2, category=category)

    response = admin_client.get("/api/inventory/equipment/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["name"] == "Trangia stove"
    assert item["category"] == "Cooking"
    assert item["quantity"] == 5
    assert item["broken_quantity"] == 2
    assert item["available_quantity"] == 3


@pytest.mark.django_db
def test_equipment_list_ordered_by_category_then_name(admin_client):
    tents = Category.objects.create(name="Tents")
    cooking = Category.objects.create(name="Cooking")
    Equipment.objects.create(name="Dome tent", short_code="X75", category=tents)
    Equipment.objects.create(name="Trangia stove", category=cooking)

    response = admin_client.get("/api/inventory/equipment/")

    names = [item["name"] for item in response.json()]
    assert names == ["Trangia stove", "Dome tent"]
