import pytest
from django.urls import reverse

from kava_varasto.inventory.models import DEFAULT_LOCATION_NAME, StorageLocation


@pytest.mark.django_db
def test_equipment_add_form_preselects_kolo(admin_client):
    location = StorageLocation.objects.get(name=DEFAULT_LOCATION_NAME)

    response = admin_client.get(reverse("admin:inventory_equipment_add"))

    assert response.status_code == 200
    assert response.context["adminform"].form.initial["location"] == location.pk


@pytest.mark.django_db
def test_equipment_add_form_renders_without_kolo(admin_client):
    StorageLocation.objects.get(name=DEFAULT_LOCATION_NAME).delete()

    response = admin_client.get(reverse("admin:inventory_equipment_add"))

    assert response.status_code == 200
    assert "location" not in response.context["adminform"].form.initial
