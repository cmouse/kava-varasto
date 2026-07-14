from datetime import timedelta

from django.db import transaction
from django.db.models import F, Prefetch, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from kava_varasto.inventory.models import Equipment

from .models import Loan, LoanItem
from .serializers import LoanableEquipmentSerializer, LoanCreateSerializer, LoanReturnSerializer, LoanSerializer


ARCHIVE_AFTER = timedelta(days=61)  # ~2 months


class LoanListCreateView(ListCreateAPIView):
    queryset = Loan.objects.prefetch_related("items__equipment__category").all()

    def get_queryset(self):
        qs = super().get_queryset()
        cutoff = timezone.now() - ARCHIVE_AFTER
        if self.request.query_params.get("archived") == "true":
            return qs.filter(returned_at__lt=cutoff)
        return qs.filter(Q(returned_at__isnull=True) | Q(returned_at__gte=cutoff))

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
        with transaction.atomic():
            loan = get_object_or_404(Loan.objects.select_for_update(), pk=pk)
            if loan.is_returned:
                return Response(
                    {"detail": _("This loan has already been returned.")}, status=status.HTTP_400_BAD_REQUEST
                )

            serializer = LoanReturnSerializer(data=request.data, context={"loan": loan, "request": request})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response(LoanSerializer(loan).data, status=status.HTTP_200_OK)


class LoanableEquipmentListView(ListAPIView):
    serializer_class = LoanableEquipmentSerializer
    queryset = (
        Equipment.objects.select_related("category", "image")
        .annotate(
            out_quantity=Coalesce(Sum(F("loan_items__quantity") - F("loan_items__quantity_returned")), Value(0))
        )
        .annotate(loanable_quantity=F("quantity") - F("broken_quantity") - F("out_quantity"))
        .prefetch_related(
            Prefetch(
                "loan_items",
                queryset=LoanItem.objects.filter(
                    loan__returned_at__isnull=True,
                    quantity_returned__lt=F("quantity"),
                ),
                to_attr="active_loan_items",
            )
        )
        .order_by("category__name", "name")
    )
