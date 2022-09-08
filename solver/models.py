from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

from solver import domain


def user_to_domain(user):
    return domain.User(user.id, user.username)


def user_from_domain(user):
    User = get_user_model()
    return User.objects.get(id=user.id)


class Schedule(models.Model):
    owner = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name="my_schedules",
        on_delete=models.PROTECT,
    )
    users = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL, related_name="schedules", blank=True
    )

    def to_domain(self):
        owner = user_to_domain(self.owner)
        s = domain.Schedule(owner=owner, id=self.id)
        [s.add_day(d.start) for d in self.day_set.all()]
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
        participants = [
            Participant.objects.create(schedule_id=obj.id, name=name)
            for name in s.participants
        ]
        # persist preferred and assigned dates
        ids = {p.name: p.id for p in participants}
        PreferredDate.objects.filter(participant__schedule_id=obj.id).delete()
        PreferredDate.objects.bulk_create(
            PreferredDate(participant_id=ids[name], start=date)
            for name, dates in s.preferences.items()
            for date in dates
        )
        AssignedDate.objects.filter(participant__schedule_id=obj.id).delete()
        AssignedDate.objects.bulk_create(
            AssignedDate(participant_id=ids[name], start=date)
            for name, date in s.assignments
        )
        # update id on domain object
        s.id = obj.id
        return s


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
