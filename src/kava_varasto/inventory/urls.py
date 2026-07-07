from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("equipment/", views.EquipmentListView.as_view(), name="equipment-list"),
]
