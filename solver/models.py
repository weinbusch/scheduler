from django.conf import settings
from django.db import models
from django.urls import reverse

from solver.utils import date_range
from solver.solver import get_schedule


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


class Schedule(models.Model):
    start = models.DateField()
    end = models.DateField()
    users = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL, related_name="schedules"
    )

    def days(self):
        return [d for d in date_range(self.start, self.end) if d.weekday() < 5]

    def solve(self):
        return get_schedule(
            self.days(),
            [u.username for u in self.users.all()],
            {
                u.username: u.user_preferences.get_available_dates(
                    start=self.start, end=self.end
                )
                for u in self.users.all()
            },
        )
