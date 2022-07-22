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
                start__gte=start,
                start__lte=end,
            )
        ]


class DayPreference(models.Model):

    user_preferences = models.ForeignKey(
        UserPreferences,
        on_delete=models.CASCADE,
        related_name="day_preferences",
    )

    start = models.DateField()

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
        to=settings.AUTH_USER_MODEL, related_name="schedules", blank=True
    )

    def days(self):
        return [d for d in date_range(self.start, self.end) if d.weekday() < 5]

    def solve(self):
        available_dates = {
            u: u.user_preferences.get_available_dates(self.start, self.end)
            for u in self.users.all()
        }
        solution = get_schedule(
            self.days(),
            available_dates,
        )
        self.assignments.all().delete()
        return Assignment.objects.bulk_create(
            [Assignment(schedule=self, user=u, date=d) for u, d in solution]
        )

    def get_absolute_url(self):
        return reverse("schedule", args=[self.pk])


class Assignment(models.Model):
    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="assignments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    date = models.DateField()
