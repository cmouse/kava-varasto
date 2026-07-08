from django.db import transaction
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from kava_varasto.inventory.models import Equipment

from .models import Loan
from .serializers import LoanableEquipmentSerializer, LoanCreateSerializer, LoanReturnSerializer, LoanSerializer


class LoanListCreateView(ListCreateAPIView):
    queryset = Loan.objects.prefetch_related("items__equipment__category").all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LoanCreateSerializer
        return LoanSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan = serializer.save()
        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)


class LoanDetailView(RetrieveAPIView):
    queryset = Loan.objects.prefetch_related("items__equipment__category").all()
    serializer_class = LoanSerializer


class LoanReturnView(APIView):
    def post(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        if loan.is_returned:
            return Response({"detail": _("This loan has already been returned.")}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LoanReturnSerializer(data=request.data, context={"loan": loan, "request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()

        return Response(LoanSerializer(loan).data, status=status.HTTP_200_OK)


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
