from rest_framework import viewsets, filters
from .models import TimesheetEntry
from .serializers import TimesheetEntrySerializer
from django_filters.rest_framework import DjangoFilterBackend

class TimesheetEntryViewSet(viewsets.ModelViewSet):
    queryset = TimesheetEntry.objects.all()
    serializer_class = TimesheetEntrySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'date']
    ordering_fields = ['date']

