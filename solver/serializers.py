from rest_framework import serializers

from solver.models import DayPreference


class DayPreferenceSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source="get_absolute_url", read_only=True)

    class Meta:

        model = DayPreference
        fields = ["id", "start", "allowed", "url"]