from rest_framework import serializers

from solver.models import DayPreference


class DayPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayPreference
        fields = ["id", "start", "allowed"]
