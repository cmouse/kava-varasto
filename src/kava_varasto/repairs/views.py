from django.utils.translation import gettext_lazy as _
from rest_framework import status as http_status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from .models import OPEN_STATUSES, RepairTicket, TicketStatus
from .serializers import RepairTicketSerializer, RepairTicketWriteSerializer

ALL_STATUSES = "all"


class RepairTicketQuerysetMixin:
    queryset = RepairTicket.objects.select_related("reported_by", "resolved_by").prefetch_related(
        "equipment"
    )


class RepairTicketListCreateView(RepairTicketQuerysetMixin, ListCreateAPIView):
    def get_queryset(self):
        qs = super().get_queryset()
        wanted = self.request.query_params.get("status")
        if wanted is None:
            # The queue is a to-do list: closed tickets are history, and only
            # ?status=all (or one explicit status) digs them back up.
            return qs.filter(status__in=OPEN_STATUSES)
        if wanted == ALL_STATUSES:
            return qs
        if wanted not in TicketStatus.values:
            # A multi-valued enum can't do what ?archived=true does and treat
            # an unknown value as "the other branch" -- a typo would silently
            # look like an empty queue.
            raise ValidationError({"status": _("Unknown status.")})
        return qs.filter(status=wanted)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RepairTicketWriteSerializer
        return RepairTicketSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response(RepairTicketSerializer(ticket).data, status=http_status.HTTP_201_CREATED)


class RepairTicketDetailView(RepairTicketQuerysetMixin, RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return RepairTicketWriteSerializer
        return RepairTicketSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_object(), data=request.data, partial=kwargs.pop("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response(RepairTicketSerializer(ticket).data)
