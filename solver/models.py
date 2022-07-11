from django.conf import settings
from django.db import models
from django.urls import reverse

from solver.utils import date_range


weekdays = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class UserPreferences(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_preferences",
    )
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)

    def is_available(self, date):
        return getattr(self, weekdays[date.weekday()], False)

    def get_available_dates(self, start, end):
        weekly = {d for d in date_range(start, end) if self.is_available(d)}
        qs = self.day_preferences.filter(start__gte=start, start__lte=end)
        allowed = set(d.start for d in qs if d.available)
        excluded = set(d.start for d in qs if not d.available)
        return list(sorted((weekly | allowed) - excluded))


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
