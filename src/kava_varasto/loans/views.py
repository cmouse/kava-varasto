from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response

from kava_varasto.inventory.models import Equipment

from .models import Loan
from .serializers import LoanableEquipmentSerializer, LoanCreateSerializer, LoanSerializer


class LoanCreateView(CreateAPIView):
    queryset = Loan.objects.all()
    serializer_class = LoanCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan = serializer.save()
        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)


class LoanableEquipmentListView(ListAPIView):
    serializer_class = LoanableEquipmentSerializer
    queryset = (
        Equipment.objects.select_related("category")
        .annotate(
            out_quantity=Coalesce(Sum(F("loan_items__quantity") - F("loan_items__quantity_returned")), Value(0))
        )
        .annotate(loanable_quantity=F("quantity") - F("broken_quantity") - F("out_quantity"))
        .order_by("category__name", "name")
    )
