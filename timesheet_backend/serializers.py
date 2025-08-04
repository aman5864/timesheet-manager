from rest_framework import serializers
from .models import TimesheetEntry

class TimesheetEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimesheetEntry
        fields = '__all__'