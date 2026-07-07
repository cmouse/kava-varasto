import pytest
from django.db import IntegrityError

from kava_varasto.inventory.models import Category


@pytest.mark.django_db
def test_category_str_is_name():
    category = Category.objects.create(name="Tents")
    assert str(category) == "Tents"


@pytest.mark.django_db
def test_category_name_unique():
    Category.objects.create(name="Tents")
    with pytest.raises(IntegrityError):
        Category.objects.create(name="Tents")
