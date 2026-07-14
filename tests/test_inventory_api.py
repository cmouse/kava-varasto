import pytest
from django.test import override_settings

from kava_varasto.inventory.models import Category, Equipment, EquipmentImage


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
def test_equipment_without_image_serializes_none(admin_client):
    category = Category.objects.create(name="Cooking")
    Equipment.objects.create(name="Trangia stove", category=category)

    response = admin_client.get("/api/inventory/equipment/")

    assert response.json()[0]["image"] is None


@pytest.mark.django_db
def test_equipment_image_returns_media_url(admin_client):
    category = Category.objects.create(name="Tents")
    image = EquipmentImage.objects.create(name="tent", image="equipment/tent.jpg")
    Equipment.objects.create(name="Dome tent", category=category, image=image)

    response = admin_client.get("/api/inventory/equipment/")

    assert response.json()[0]["image"] == "/media/equipment/tent.jpg"


@pytest.mark.django_db
@override_settings(MEDIA_URL="/varasto/media/")
def test_equipment_image_honors_media_url_prefix(admin_client):
    category = Category.objects.create(name="Tents")
    image = EquipmentImage.objects.create(name="tent", image="equipment/tent.jpg")
    Equipment.objects.create(name="Dome tent", category=category, image=image)

    response = admin_client.get("/api/inventory/equipment/")

    assert response.json()[0]["image"] == "/varasto/media/equipment/tent.jpg"


@pytest.mark.django_db
def test_equipment_image_shared_between_equipment(admin_client):
    category = Category.objects.create(name="Cooking")
    image = EquipmentImage.objects.create(name="stove", image="equipment/stove.jpg")
    Equipment.objects.create(name="Trangia stove", category=category, image=image)
    Equipment.objects.create(name="Trangia stove XL", category=category, image=image)

    response = admin_client.get("/api/inventory/equipment/")

    urls = [item["image"] for item in response.json()]
    assert urls == ["/media/equipment/stove.jpg", "/media/equipment/stove.jpg"]


@pytest.mark.django_db
def test_equipment_list_ordered_by_category_then_name(admin_client):
    tents = Category.objects.create(name="Tents")
    cooking = Category.objects.create(name="Cooking")
    Equipment.objects.create(name="Dome tent", short_code="X75", category=tents)
    Equipment.objects.create(name="Trangia stove", category=cooking)

    response = admin_client.get("/api/inventory/equipment/")

    names = [item["name"] for item in response.json()]
    assert names == ["Trangia stove", "Dome tent"]
