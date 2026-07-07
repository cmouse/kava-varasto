from rest_framework.generics import ListAPIView

from .models import Equipment
from .serializers import EquipmentSerializer


class EquipmentListView(ListAPIView):
    queryset = Equipment.objects.select_related("category").order_by("category__name", "name")
    serializer_class = EquipmentSerializer
