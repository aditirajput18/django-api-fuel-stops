from rest_framework import serializers
from .models import FuelStation

class FuelStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelStation
        fields = ['external_id', 'name', 'lat', 'lon', 'price']
