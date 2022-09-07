import pytest
import json
import datetime
from unittest.mock import patch

from django.urls import reverse

from solver.models import user_to_domain
from solver.repository import ScheduleRepository
from solver.domain import Schedule, ScheduleException


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    # https://pytest-django.readthedocs.io/en/latest/configuring_django.html#overriding-individual-settings
    # https://docs.djangoproject.com/en/4.0/topics/testing/overview/#password-hashing
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_user(username="owner", password="1234")


@pytest.fixture
def other(django_user_model):
    return django_user_model.objects.create_user(username="other", password="1234")


@pytest.fixture
def repo():
    return ScheduleRepository()


@pytest.fixture
def schedule(repo, owner):
    s = Schedule(owner=user_to_domain(owner))
    s = repo.add(s)
    return s


def test_day_list(client, repo, owner):
    schedule = Schedule(owner=user_to_domain(owner))
    dates = [datetime.date(2022, 1, d) for d in range(1, 7)]
    for date in dates:
        schedule.add_day(date)
    repo.add(schedule)
    client.force_login(owner)
    r = client.get(reverse("api:schedule_days", args=[schedule.id]))
    assert json.loads(r.content) == [{"start": date.isoformat()} for date in dates]


def test_add_day(repo, schedule, client, owner):
    client.force_login(owner)
    r = client.patch(
        reverse("api:schedule_days", args=[schedule.id]),
        data={"date": "2022-01-01"},
        content_type="application/json",
    )
    assert r.status_code == 204
    s = repo.get(schedule.id)
    assert datetime.date(2022, 1, 1) in s.days


def test_add_day_invalid_date(repo, schedule, client, owner):
    client.force_login(owner)
    r = client.patch(
        reverse("api:schedule_days", args=[schedule.id]),
        data={"start": "invalid-date"},
        content_type="application/json",
    )
    assert r.status_code == 400


def test_remove_day(repo, schedule, client, owner):
    schedule.add_day(datetime.date(2022, 1, 1))
    repo.add(schedule)
    client.force_login(owner)
    r = client.delete(
        reverse("api:schedule_days", args=[schedule.id]),
        data={"date": "2022-01-01"},
        content_type="application/json",
    )
    assert r.status_code == 204
    s = repo.get(schedule.id)
    assert datetime.date(2022, 1, 1) not in s.days


def test_day_list_unauthenticated(schedule, client):
    r = client.get(reverse("api:schedule_days", args=[schedule.id]))
    assert r.status_code == 403


def test_day_list_unauthorized(schedule, client, other):
    client.force_login(other)
    r = client.get(reverse("api:schedule_days", args=[schedule.id]))
    assert r.status_code == 403


def test_preferences_list(client, schedule, repo, owner):
    dates = [datetime.date(2022, 1, d) for d in range(1, 7)]
    for date in dates:
        schedule.add_preference("foo", date)
    repo.add(schedule)
    client.force_login(owner)
    r = client.get(reverse("api:schedule_preferences", args=[schedule.id]))
    assert json.loads(r.content) == [
        {"participant": "foo", "start": date.isoformat()} for date in dates
    ]


def test_add_preference(client, schedule, repo, owner):
    client.force_login(owner)
    r = client.patch(
        reverse("api:schedule_preferences", args=[schedule.id]),
        data={"name": "foo", "date": "2022-01-01"},
        content_type="application/json",
    )
    assert r.status_code == 204
    s = repo.get(schedule.id)
    assert s.preferences == {"foo": {datetime.date(2022, 1, 1)}}


def test_delete_preference(client, schedule, repo, owner):
    schedule.add_preference("foo", datetime.date(2022, 1, 1))
    repo.add(schedule)
    client.force_login(owner)
    r = client.delete(
        reverse("api:schedule_preferences", args=[schedule.id]),
        data={"name": "foo", "date": "2022-01-01"},
        content_type="application/json",
    )
    assert r.status_code == 204
    s = repo.get(schedule.id)
    assert s.preferences == {"foo": set()}


def test_preferences_list_unauthenticated(schedule, client):
    r = client.get(reverse("api:schedule_preferences", args=[schedule.id]))
    assert r.status_code == 403


def test_preferences_list_unauthorized(schedule, client, other):
    client.force_login(other)
    r = client.get(reverse("api:schedule_preferences", args=[schedule.id]))
    assert r.status_code == 403


def test_assignments_list(repo, schedule, client, owner):
    dates = [datetime.date(2022, 1, d) for d in range(1, 7)]
    for date in dates:
        schedule.add_preference("foo", date)
        schedule.add_assignment("foo", date)
    schedule = repo.add(schedule)
    client.force_login(owner)
    r = client.get(reverse("api:schedule_assignments", args=[schedule.id]))
    assert json.loads(r.content) == [
        {"participant": "foo", "start": date.isoformat()} for date in dates
    ]


def test_assignments_list_unauthenticated(schedule, client):
    r = client.get(reverse("api:schedule_assignments", args=[schedule.id]))
    assert r.status_code == 403


def test_assignments_list_unauthorized(schedule, client, other):
    client.force_login(other)
    r = client.get(reverse("api:schedule_assignments", args=[schedule.id]))
    assert r.status_code == 403


@pytest.mark.parametrize(
    "url_name",
    [
        "api:schedule",
        "api:schedule_days",
        "api:schedule_preferences",
        "api:schedule_assignments",
    ],
)
def test_schedule_404(client, owner, url_name):
    client.force_login(owner)
    url = reverse(url_name, args=[99])
    r = client.get(url)
    assert r.status_code == 404


def test_patch_schedule_calls_make_assignments_returns_204(schedule, client, owner):
    client.force_login(owner)
    with patch.object(Schedule, "make_assignments") as f:
        r = client.patch(reverse("api:schedule", args=[schedule.id]))
        assert r.status_code == 204
        f.assert_called_once()


def test_patch_persists_schedule(schedule, client, owner, repo):
    client.force_login(owner)
    schedule.add_preference("foo", datetime.date(2022, 1, 1))
    repo.add(schedule)
    solution = [(datetime.date(2022, 1, 1), "foo")]
    with patch("solver.domain.get_schedule", return_value=solution):
        client.patch(reverse("api:schedule", args=[schedule.id]))
    s = repo.get(schedule.id)
    assert s.assignments == {("foo", datetime.date(2022, 1, 1))}


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
def test_schedule_method_not_allowed(schedule, client, owner, method):
    client.force_login(owner)
    url = reverse("api:schedule", args=[schedule.id])
    r = getattr(client, method)(url)
    assert r.status_code == 405


def test_patch_schedule_specific_exception(schedule, client, owner):
    client.force_login(owner)
    with patch.object(
        Schedule, "make_assignments", side_effect=ScheduleException("foo")
    ):
        r = client.patch(reverse("api:schedule", args=[schedule.id]))
        assert r.status_code == 500
        assert json.loads(r.content) == {"error": "foo"}


def test_patch_schedule_unspecific_exception(schedule, client, owner):
    client.force_login(owner)
    with patch.object(Schedule, "make_assignments", side_effect=Exception):
        with pytest.raises(Exception):
            client.patch(reverse("api:schedule", args=[schedule.id]))


def test_patch_schedule_unauthenticated(schedule, client):
    r = client.get(reverse("api:schedule", args=[schedule.id]))
    assert r.status_code == 403


def test_patch_schedule_unauthorized(schedule, client, other):
    client.force_login(other)
    r = client.get(reverse("api:schedule", args=[schedule.id]))
    assert r.status_code == 403
