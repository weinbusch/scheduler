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
            obj = (
                cls.objects.select_related("owner")
                .prefetch_related("day_set")
                .prefetch_related("participant_set")
                .prefetch_related("participant_set__preferreddate_set")
                .prefetch_related("participant_set__assigneddate_set")
                .get(id=s.id)
            )
        except cls.DoesNotExist:
            obj = cls()

        # persist Schedule
        obj.owner = user_from_domain(s.owner)
        obj.window = s.window
        obj.save()

        # update id on domain object
        s.id = obj.id

        # persist Days
        saved_days = {d.start for d in obj.day_set.all()}

        if deleted_days := (saved_days - s.days):
            Day.objects.filter(schedule_id=obj.id).filter(
                start__in=deleted_days
            ).delete()

        if new_days := (s.days - saved_days):
            Day.objects.bulk_create(
                [Day(schedule_id=obj.id, start=date) for date in new_days]
            )

        # persist Participants
        saved_participants = {p.name: p for p in obj.participant_set.all()}

        if deleted_participants := {
            p for name, p in saved_participants.items() if name not in s.participants
        }:
            Participant.objects.filter(
                schedule_id=obj.id, id__in=[p.id for p in deleted_participants]
            ).delete()

        for name in s.participants:
            participant = saved_participants.get(name, None)

            if participant:
                preferred_dates = s.preferences[name]
                saved_preferred_dates = {
                    d.start for d in participant.preferreddate_set.all()
                }

                if deleted_preferred_dates := saved_preferred_dates - preferred_dates:
                    PreferredDate.objects.filter(
                        participant=participant, start__in=deleted_preferred_dates
                    ).delete()

                if new_preferred_dates := preferred_dates - saved_preferred_dates:
                    PreferredDate.objects.bulk_create(
                        PreferredDate(participant=participant, start=d)
                        for d in new_preferred_dates
                    )

                assigned_dates = {d for n, d in s.assignments if n == name}
                saved_assigned_dates = {
                    d.start for d in participant.assigneddate_set.all()
                }
                if deleted_assigned_dates := saved_assigned_dates - assigned_dates:
                    AssignedDate.objects.filter(
                        participant=participant, start__in=deleted_assigned_dates
                    ).delete()
                if new_assigned_dates := assigned_dates - saved_assigned_dates:
                    AssignedDate.objects.bulk_create(
                        AssignedDate(participant=participant, start=d)
                        for d in new_assigned_dates
                    )
            else:
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
