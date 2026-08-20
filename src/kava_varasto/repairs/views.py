from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status as http_status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from .models import OPEN_STATUSES, RepairTicket, TicketStatus
from .serializers import RepairTicketSerializer, RepairTicketWriteSerializer

ALL_STATUSES = "all"
RECENT_RESOLVED = "recent"
# How long a closed ticket stays in the "show resolved" view. Longer than the
# loans' ARCHIVE_AFTER on purpose: gear is seasonal, and "did we already fix
# this last autumn?" has to stay answerable without digging through history.
RESOLVED_VISIBLE_FOR = timedelta(days=365)


class RepairTicketQuerysetMixin:
    queryset = RepairTicket.objects.select_related("reported_by", "resolved_by").prefetch_related(
        "equipment"
    )


class RepairTicketListCreateView(RepairTicketQuerysetMixin, ListCreateAPIView):
    def get_queryset(self):
        qs = super().get_queryset()
        wanted = self.request.query_params.get("status")
        resolved = self.request.query_params.get("resolved")
        if resolved is not None and resolved != RECENT_RESOLVED:
            raise ValidationError({"resolved": _("Unknown value.")})
        if wanted is None:
            if resolved == RECENT_RESOLVED:
                # What the SPA's "show resolved" checkbox asks for: the queue
                # plus what was dealt with recently enough to still be worth
                # reading. Anything older is history and needs ?status=all.
                cutoff = timezone.now() - RESOLVED_VISIBLE_FOR
                return qs.filter(Q(status__in=OPEN_STATUSES) | Q(resolved_at__gte=cutoff))
            # The queue is a to-do list: closed tickets are history, and only
            # ?resolved=recent or ?status=all digs them back up.
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
