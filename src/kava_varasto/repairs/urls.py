from django.urls import path

from . import views

app_name = "repairs"

urlpatterns = [
    path("", views.RepairTicketListCreateView.as_view(), name="ticket-list-create"),
    path("<int:pk>/", views.RepairTicketDetailView.as_view(), name="ticket-detail"),
]
