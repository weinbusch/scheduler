from django.conf import settings
from django.db import models
from django.urls import reverse


class UserPreferences(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_preferences",
    )

    def get_available_dates(self, start, end):
        return [
            d.start
            for d in self.day_preferences.filter(
                start__gte=start, start__lte=end, available=True
            )
        ]


class DayPreference(models.Model):

    user_preferences = models.ForeignKey(
        UserPreferences,
        on_delete=models.CASCADE,
        related_name="day_preferences",
    )

    start = models.DateField()

    available = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse("day_preference", args=[self.id])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_preferences", "start"],
                name="unique_day_preference",
            )
        ]
