import datetime

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

from solver.utils import date_range
from solver.solver import get_schedule
from solver import domain


def user_to_domain(user):
    return domain.User(user.id, user.username)


def user_from_domain(user):
    User = get_user_model()
    return User.objects.get(id=user.id)


def get_available_dates(user, schedule, start, end):
    return [
        d.start
        for d in user.day_preferences.filter(
            schedule=schedule,
            start__gte=start,
            start__lte=end,
            active=True,
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

    active = models.BooleanField(default=True)

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
    owner = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name="my_schedules",
        on_delete=models.PROTECT,
    )

    def to_domain(self):
        owner = user_to_domain(self.owner)
        s = domain.Schedule(owner=owner, id=self.id)
        s.days = {d.start for d in self.day_set.all()}
        participants = self.participant_set.all()
        for participant in participants:
            s.add_participant(participant.name)
            for date in participant.preferreddate_set.all():
                s.add_preference(participant.name, date.start)
            for date in participant.assigneddate_set.all():
                s.add_assignment(participant.name, date.start)
        return s

    @classmethod
    def update_from_domain(cls, s):
        try:
            obj = cls.objects.get(id=s.id)
        except cls.DoesNotExist:
            obj = cls()
        owner = user_from_domain(s.owner)
        obj.owner = owner
        obj.save()
        # persist days
        Day.objects.filter(schedule_id=obj.id).delete()
        Day.objects.bulk_create(
            [Day(schedule_id=obj.id, start=date) for date in s.days]
        )
        # persist participants
        Participant.objects.filter(schedule_id=obj.id).delete()
        participants = Participant.objects.bulk_create(
            [Participant(schedule_id=obj.id, name=name) for name in s.participants]
        )
        # persist preferred and assigned dates
        ids = {p.name: p.id for p in participants}
        PreferredDate.objects.filter(participant_id__in=ids.values()).delete()
        PreferredDate.objects.bulk_create(
            [
                PreferredDate(participant_id=ids[name], start=date)
                for name, dates in s.preferences.items()
                for date in dates
            ]
        )
        AssignedDate.objects.filter(participant_id__in=ids.values()).delete()
        AssignedDate.objects.bulk_create(
            [
                AssignedDate(participant_id=ids[name], start=date)
                for name, dates in s.preferences.items()
                for date in dates
            ]
        )
        # update id on domain object
        s.id = obj.id
        return s

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
        finally:
            self.assignments.all().delete()
        return Assignment.objects.bulk_create(
            [Assignment(schedule=self, user=u, start=d) for d, u in solution]
        )

    def get_absolute_url(self):
        return reverse("schedule_settings", args=[self.pk])

    @property
    def has_assignments(self):
        return self.assignments.count() > 0


class Day(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    start = models.DateField()


class Participant(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["schedule_id", "name"],
                name="unique_participant",
            )
        ]


class PreferredDate(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    start = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["participant_id", "start"],
                name="unique_preferred_date",
            )
        ]


class AssignedDate(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    start = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["participant_id", "start"],
                name="unique_assigned_date",
            )
        ]


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["start", "schedule"],
                name="unique_assignment",
            )
        ]
