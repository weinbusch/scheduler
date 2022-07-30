import datetime

from django.conf import settings
from django.db import models
from django.urls import reverse

from solver.utils import date_range
from solver.solver import get_schedule


def get_available_dates(user, schedule, start, end):
    return [
        d.start
        for d in user.day_preferences.filter(
            schedule=schedule,
            start__gte=start,
            start__lte=end,
        )
    ]


class DayPreference(models.Model):

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="day_preferences",
    )

    schedule = models.ForeignKey(
        to="Schedule",
        on_delete=models.CASCADE,
        related_name="day_preferences",
    )

    start = models.DateField()

    def get_absolute_url(self):
        return reverse("api:day_preference", args=[self.id])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "start", "schedule"],
                name="unique_day_preference",
            )
        ]


class ScheduleException(Exception):
    pass


class Schedule(models.Model):
    start = models.DateField(default=datetime.date.today)
    end = models.DateField(default=datetime.date.today)
    users = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL, related_name="schedules", blank=True
    )

    def days(self):
        return [d for d in date_range(self.start, self.end) if d.weekday() < 5]

    def solve(self):
        available_dates = {
            u: get_available_dates(u, self, self.start, self.end)
            for u in self.users.all()
        }
        try:
            solution = get_schedule(
                self.days(),
                available_dates,
            )
        except Exception as e:
            raise ScheduleException(e)
        self.assignments.all().delete()
        return Assignment.objects.bulk_create(
            [Assignment(schedule=self, user=u, start=d) for d, u in solution]
        )

    def get_absolute_url(self):
        return reverse("schedule", args=[self.pk])

    @property
    def has_assignments(self):
        return self.assignments.count() > 0


class Assignment(models.Model):
    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="assignments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    start = models.DateField()
