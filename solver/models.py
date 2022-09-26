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
    window = models.IntegerField(null=True)

    def to_domain(self):
        owner = user_to_domain(self.owner)
        s = domain.Schedule(owner=owner, id=self.id, window=self.window)
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
        obj.window = s.window
        obj.save()
        # update id on domain object
        s.id = obj.id
        # persist days
        saved_days = {d.start for d in obj.day_set.all()}
        if orphan_days := (saved_days - s.days):
            Day.objects.filter(schedule_id=obj.id).filter(
                start__in=orphan_days
            ).delete()
        if new_days := (s.days - saved_days):
            Day.objects.bulk_create(
                [Day(schedule_id=obj.id, start=date) for date in new_days]
            )
        # persist participants
        saved_participants = list(obj.participant_set.all())
        saved_participant_names = [p.name for p in saved_participants]
        if orphan_participants := {
            p for p in saved_participants if p.name not in s.participants
        }:
            Participant.objects.filter(
                schedule_id=obj.id, id__in=[p.id for p in orphan_participants]
            ).delete()
        for name in s.participants:
            if name not in saved_participant_names:
                participant = Participant.objects.create(schedule=obj, name=name)
                PreferredDate.objects.bulk_create(
                    PreferredDate(participant_id=participant.id, start=date)
                    for date in s.preferences[name]
                )
                AssignedDate.objects.bulk_create(
                    AssignedDate(participant_id=participant.id, start=date)
                    for n, date in s.assignments
                    if n == name
                )
            else:
                participant = next(p for p in saved_participants if p.name == name)
                # update preferred dates
                preferred_dates = s.preferences[name]
                saved_preferred_dates = {
                    d.start for d in participant.preferreddate_set.all()
                }
                if orphan_preferred_dates := saved_preferred_dates - preferred_dates:
                    PreferredDate.objects.filter(
                        participant=participant, start__in=orphan_preferred_dates
                    ).delete()
                if new_preferred_dates := preferred_dates - saved_preferred_dates:
                    PreferredDate.objects.bulk_create(
                        PreferredDate(participant=participant, start=d)
                        for d in new_preferred_dates
                    )
                # update assigned dates
                assigned_dates = {d for n, d in s.assignments if n == name}
                saved_assigned_dates = {
                    d.start for d in participant.assigneddate_set.all()
                }
                if orphan_assigned_dates := saved_assigned_dates - assigned_dates:
                    AssignedDate.objects.filter(
                        participant=participant, start__in=orphan_assigned_dates
                    ).delete()
                if new_assigned_dates := assigned_dates - saved_assigned_dates:
                    AssignedDate.objects.bulk_create(
                        AssignedDate(participant=participant, start=d)
                        for d in new_assigned_dates
                    )
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
