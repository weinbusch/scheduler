import pytest
import datetime

from django.contrib.auth import get_user_model

from solver import domain
from solver import models
from solver.repository import ScheduleRepository


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    # https://pytest-django.readthedocs.io/en/latest/configuring_django.html#overriding-individual-settings
    # https://docs.djangoproject.com/en/4.0/topics/testing/overview/#password-hashing
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]


def create_user(username):
    User = get_user_model()
    return User.objects.create_user(username, password="123")


def create_schedule(owner):
    return models.Schedule.objects.create(owner=owner)


@pytest.mark.django_db
def test_get_schedule_list():
    owner = create_user("owner")
    other = create_user("other")
    create_schedule(owner)
    create_schedule(other)
    schedules = ScheduleRepository().list()
    assert len(schedules) == 2
    assert isinstance(schedules[0], domain.Schedule)


@pytest.mark.django_db
def test_filter_list_for_owner():
    owner = create_user("owner")
    other = create_user("other")
    create_schedule(owner)
    create_schedule(owner)
    create_schedule(other)
    schedules = ScheduleRepository().list(owner.id)
    assert len(schedules) == 2
    assert all([s.owner.id == owner.id for s in schedules])


@pytest.mark.django_db
def test_list_for_unknown_user():
    owner = create_user("owner")
    create_schedule(owner)
    schedules = ScheduleRepository().list(owner.id + 1)
    assert schedules == []


@pytest.mark.django_db
def test_get_schedule():
    u1 = create_user("u1")
    s1 = create_schedule(owner=u1)
    u2 = create_user("u2")
    create_schedule(owner=u2)
    s = ScheduleRepository().get(s1.pk)
    assert isinstance(s, domain.Schedule)


@pytest.mark.django_db
def test_schedule_does_not_exist():
    s = ScheduleRepository().get(99)
    assert s is None


@pytest.mark.django_db
def test_add_get_schedule_roundtrip():
    u = create_user("owner")
    s = domain.Schedule(
        owner=domain.User(u.pk, "owner"),
        start=datetime.date(2022, 1, 1),
        end=datetime.date(2022, 1, 8),
    )
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_preference("foo", datetime.date(2022, 1, 2))
    s.add_assignment("foo", datetime.date(2022, 1, 2))
    repo = ScheduleRepository()
    s = repo.add(s)
    t = repo.get(s.id)
    assert t.owner.id == u.pk
    assert t.days == {datetime.date(2022, 1, d) for d in range(1, 8)}
    assert t.preferences == {
        "foo": {datetime.date(2022, 1, 1), datetime.date(2022, 1, 2)}
    }
    assert t.assignments == {("foo", datetime.date(2022, 1, 2))}


@pytest.mark.django_db
def test_modify_schedule():
    repo = ScheduleRepository()
    user = create_user("user")
    s = domain.Schedule(
        owner=domain.User(user.pk, "owner"),
        start=datetime.date(2022, 1, 1),
        end=datetime.date(2022, 1, 7),
    )
    t = repo.add(s)
    t.remove_day(datetime.date(2022, 1, 6))
    t.add_day(datetime.date(2022, 1, 9))
    repo.add(t)
    u = repo.get(t.id)
    assert datetime.date(2022, 1, 6) not in u.days
    assert datetime.date(2022, 1, 9) in u.days


@pytest.mark.django_db
def test_delete_schedule():
    repo = ScheduleRepository()
    user = create_user("user")
    s = domain.Schedule(
        owner=domain.User(user.pk, "owner"),
        start=datetime.date(2022, 1, 1),
        end=datetime.date(2022, 1, 7),
    )
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_assignment("foo", datetime.date(2022, 1, 1))
    s = repo.add(s)
    repo.delete(s)
    assert repo.get(s.id) is None
