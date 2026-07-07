from django.urls import path

from . import views

app_name = "loans"

urlpatterns = [
    path("", views.LoanCreateView.as_view(), name="loan-create"),
    path("loanable-equipment/", views.LoanableEquipmentListView.as_view(), name="loanable-equipment"),
]
