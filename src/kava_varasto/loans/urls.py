from django.urls import path

from . import views

app_name = "loans"

urlpatterns = [
    path("", views.LoanListCreateView.as_view(), name="loan-list-create"),
    path("loanable-equipment/", views.LoanableEquipmentListView.as_view(), name="loanable-equipment"),
    path("<int:pk>/", views.LoanDetailView.as_view(), name="loan-detail"),
    path("<int:pk>/return/", views.LoanReturnView.as_view(), name="loan-return"),
]
