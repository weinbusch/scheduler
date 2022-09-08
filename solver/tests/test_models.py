import pytest
import datetime

from solver import models, domain

from django.contrib.auth import get_user_model


def create_user(username):
    User = get_user_model()
    return User.objects.create_user(username=username, password="1234")


@pytest.mark.django_db
def test_schedule_to_domain():
    owner = create_user("owner")
    schedule = models.Schedule.objects.create(owner=owner)
    participant = models.Participant.objects.create(schedule=schedule, name="foo")
    models.Day.objects.bulk_create(
        models.Day(schedule=schedule, start=datetime.date(2022, 1, x))
        for x in range(1, 8)
    )
    models.PreferredDate.objects.bulk_create(
        models.PreferredDate(participant=participant, start=datetime.date(2022, 1, x))
        for x in range(1, 8)
    )
    models.AssignedDate.objects.bulk_create(
        models.AssignedDate(participant=participant, start=datetime.date(2022, 1, x))
        for x in [1, 3, 5]
    )
    obj = schedule.to_domain()
    assert obj.owner.id == owner.id
    assert obj.days == {datetime.date(2022, 1, x) for x in range(1, 8)}
    assert obj.preferences == {"foo": {datetime.date(2022, 1, x) for x in range(1, 8)}}
    assert obj.assignments == {("foo", datetime.date(2022, 1, x)) for x in [1, 3, 5]}


@pytest.mark.django_db
def test_persist_new_schedule():
    owner = create_user("owner")
    s = domain.Schedule(
        owner=domain.User(owner.id, owner.username),
        start=datetime.date(2022, 1, 1),
        end=datetime.date(2022, 1, 8),
    )
    [s.add_preference("foo", datetime.date(2022, 1, x)) for x in range(1, 5)]
    [s.add_assignment("foo", datetime.date(2022, 1, x)) for x in range(1, 4)]
    s = models.Schedule.update_from_domain(s)
    assert s.id == 1
    assert models.Schedule.objects.filter(owner=owner).count() == 1
    assert models.Day.objects.filter(schedule__owner=owner).count() == 7
    assert (
        models.Participant.objects.filter(schedule__owner=owner, name="foo").count()
        == 1
    )
    assert (
        models.PreferredDate.objects.filter(participant__schedule__owner=owner).count()
        == 4
    )
    assert (
        models.AssignedDate.objects.filter(participant__schedule__owner=owner).count()
        == 3
    )


@pytest.mark.django_db
def test_persist_updated_schedule():
    owner = create_user("owner")
    s = domain.Schedule(
        owner=domain.User(owner.id, owner.username),
        start=datetime.date(2022, 1, 1),
        end=datetime.date(2022, 1, 8),
    )
    [s.add_preference("foo", datetime.date(2022, 1, x)) for x in range(1, 5)]
    [s.add_assignment("foo", datetime.date(2022, 1, x)) for x in range(1, 4)]
    # persist schedule
    s = models.Schedule.update_from_domain(s)
    # remove preference
    s.remove_preference("foo", datetime.date(2022, 1, 1))
    s = models.Schedule.update_from_domain(s)
    assert (
        models.PreferredDate.objects.filter(
            participant__name="foo", start=datetime.date(2022, 1, 1)
        ).exists()
        is False
    )
    assert models.PreferredDate.objects.filter(participant__name="foo").count() == 3
    # add preference
    s.add_preference("foo", datetime.date(2022, 1, 9))
    s = models.Schedule.update_from_domain(s)
    assert models.PreferredDate.objects.filter(participant__name="foo").count() == 4
    # add new participant with preference
    s.add_preference("bar", datetime.date(2022, 1, 1))
    s = models.Schedule.update_from_domain(s)
    assert models.PreferredDate.objects.filter(participant__name="bar").count() == 1
    # clear assignments
    s.clear_assignments()
    s = models.Schedule.update_from_domain(s)
    assert models.AssignedDate.objects.count() == 0
