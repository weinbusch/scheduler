from rest_framework import serializers

from solver.models import DayPreference, Assignment


class DayPreferenceSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source="get_absolute_url", read_only=True)
    username = serializers.CharField(
        source="user_preferences.user.username", read_only=True
    )

    class Meta:

        model = DayPreference
        fields = [
            "id",
            "username",
            "start",
            "url",
        ]


class AssignmentSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="user.username")

    class Meta:
        model = Assignment
        fields = ["id", "username", "start"]
